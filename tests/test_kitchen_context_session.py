"""Temporary-session behavior and practical constraints; no external requests."""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from coach_web import create_coach_app, Settings
from kitchen_coach import KitchenCoach
from kitchen_context import KitchenContext
from test_coach import ORIGIN, CODE, sign_in, send, no_network
from test_kitchen_context import P, SAFE, turn

def app_fixture(generate):
    now=[1000.0]
    app=FastAPI()
    child=create_coach_app(Settings(access_code=CODE,origin=ORIGIN,ai_enabled=True,
                                   api_key="offline-fixture",model="fixture"),
                           KitchenCoach(generate),lambda:now[0])
    app.mount("/coach",child)
    return app,child,now

def test_session_remembers_no_on_reload_reset_and_clears_on_logout():
    app,child,now=app_fixture(lambda *a:SAFE)
    client=TestClient(app,base_url=ORIGIN)
    headers=sign_in(client)
    assert send(client,headers,"Help with dinner",P).status_code==200
    assert client.get("/coach/state").json()["kitchen_context"]["pending_tool"]=="thermometer"
    now[0]+=3
    response=send(client,headers,"no",P)
    assert response.status_code==200
    state=client.get("/coach/state").json()
    assert state["kitchen_context"]["tools"]["thermometer"]=="unavailable"
    assert not state["kitchen_context"]["pending_tool"]
    assert client.post("/coach/reset",json={},headers=headers).status_code==200
    state=client.get("/coach/state").json()
    assert state["history"]==[] and state["profile"]==P
    assert state["kitchen_context"]["tools"]["thermometer"]=="unavailable"
    now[0]+=3
    assert "Do you have" not in send(client,headers,"Help with dinner",P).json()["reply"]
    assert client.post("/coach/logout",json={},headers=headers).status_code==200
    assert not child.state.sessions
    sign_in(client)
    assert client.get("/coach/state").json()["kitchen_context"]["tools"]["thermometer"]=="unknown"

def test_sessions_do_not_share_answers():
    app,child,now=app_fixture(lambda *a:SAFE)
    a,b=TestClient(app,base_url=ORIGIN),TestClient(app,base_url=ORIGIN)
    ah,bh=sign_in(a),sign_in(b)
    send(a,ah,"Help with dinner",P)
    now[0]+=3
    send(a,ah,"no",P)
    send(b,bh,"Help with dinner",P)
    assert a.get("/coach/state").json()["kitchen_context"]["tools"]["thermometer"]=="unavailable"
    assert b.get("/coach/state").json()["kitchen_context"]["tools"]["thermometer"]=="unknown"

def test_failed_generation_does_not_commit_answer_or_lose_pending_question():
    calls=[]
    def generate(*a):
        calls.append(1)
        if len(calls)==2: raise RuntimeError("offline fixture")
        return SAFE
    app,child,now=app_fixture(generate)
    client=TestClient(app,base_url=ORIGIN); headers=sign_in(client)
    send(client,headers,"Help with dinner",P)
    now[0]+=3
    assert send(client,headers,"yes",P).status_code==503
    state=client.get("/coach/state").json()["kitchen_context"]
    assert state["tools"]["thermometer"]=="unknown" and state["pending_tool"]=="thermometer"

def test_no_tool_followup_can_adapt_to_rice_and_cultural_flavors():
    captured=[]
    def generate(instructions,messages,budget):
        data=json.loads(messages[0]["content"].split("\n",1)[1]); captured.append(data)
        if data["kitchen_context"]["tools"]["thermometer"]=="unavailable":
            return "Keep the Caribbean flavors in your rice: use your garlic and thyme. We can work on that shared component without cooking the raw chicken."
        return SAFE
    k,h=KitchenContext(),[]; coach=KitchenCoach(generate)
    turn(coach,k,h,"Help with dinner")
    reply=turn(coach,k,h,"no")
    assert reply.source=="model"
    assert "Caribbean" in reply.text and "rice" in reply.text
    assert captured[-1]["household"]==P["household"]

@pytest.mark.parametrize("constraints,draft,reason", [
 ("10 minutes; stove","Simmer the rice for 45 minutes.","time:exceeded"),
 ("no additional grocery purchase","Buy a blender for this sauce.","budget:no-purchase"),
 ("small budget; no shopping","Purchase specialty ingredients.","budget:no-purchase"),
])
def test_unusable_time_or_purchase_requirement_is_withheld(constraints,draft,reason):
    r=KitchenCoach(lambda *a:draft).respond({**P,"constraints":constraints},[],"Help",kitchen=KitchenContext())
    assert r.source=="kitchen_context" and r.safety_reason==reason
    assert r.text!=draft

def test_known_tool_question_is_not_repeated():
    r=KitchenCoach(lambda *a:"Do you have a blender?").respond(
        {**P,"constraints":"I have a blender"},[],"Help with sauce",kitchen=KitchenContext())
    assert "?" not in r.text and "already" in r.text

def test_no_after_unrelated_question_does_not_answer_stale_tool_question():
    k,h=KitchenContext(),[]
    coach=KitchenCoach(lambda *a:SAFE)
    turn(coach,k,h,"Help")
    h.extend([{"role":"user","content":"Different question"},
              {"role":"assistant","content":"Do you want a different meal?"}])
    k.observe(P,h,"no")
    assert k.tools["thermometer"]=="unknown"

def test_unknown_tool_question_is_not_repeated_when_unanswered():
    k,h=KitchenContext(),[]; coach=KitchenCoach(lambda *a:SAFE)
    turn(coach,k,h,"Help")
    reply=turn(coach,k,h,"I'm unsure")
    assert reply.text.count("?")==0
    assert k.tools["thermometer"]=="unknown"

def test_poultry_rinsing_block_survives_missing_tools():
    k=KitchenContext()
    r=KitchenCoach(lambda *a:"Rinse raw chicken.").respond(
        {**P,"constraints":"no thermometer; no oven"},[],"Help",kitchen=k)
    assert r.source=="food_safety_gate"
    assert "Do not wash" in r.text

def test_no_after_unsure_still_resolves_the_same_outstanding_tool():
    k,h=KitchenContext(),[]; coach=KitchenCoach(lambda *a:SAFE)
    turn(coach,k,h,"Help")
    reply=turn(coach,k,h,"I'm unsure")
    assert "?" not in reply.text
    turn(coach,k,h,"no")
    assert k.tools["thermometer"]=="unavailable"
    assert not k.pending_tool
