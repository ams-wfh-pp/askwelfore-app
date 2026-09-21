"""Small user-confirmed kitchen context; no persistence, API, or clinical inference."""
import re
from dataclasses import dataclass, field
from food_actions import analyze, poultry_cooking
from food_safety import norm, context

VERSION = "kitchen-context-v1"

TOOLS = {
 "thermometer": (r"(?:food |meat |digital )?thermometer", "food thermometer"),
 "oven": (r"oven", "oven"),
 "stove": (r"stove(?:top)?|hob", "stove"),
 "microwave": (r"microwave", "microwave"),
 "blender": (r"blender", "blender"),
 "food_processor": (r"food processor", "food processor"),
 "specialty_knife": (r"mandoline|specialty knife", "specialty cutting tool"),
}
APPLIANCES = {"oven", "stove", "microwave", "blender", "food_processor"}
ALL_NAMES = "|".join(v[0] for v in TOOLS.values())
NEG = r"(?:no|without|don't have|do not have|don't own|do not own|cannot use|can't use|no access to)"
POS = r"(?:have|own|got|can use|access to|using)"
UNKNOWN = r"\b(?:unsure|not sure|don't know|do not know|maybe|might|if i had|if we had)\b"

@dataclass(frozen=True)
class ContextDecision:
    text: str
    reason: str

@dataclass
class KitchenContext:
    tools: dict = field(default_factory=lambda: {key:"unknown" for key in TOOLS})
    pending_tool: str = ""
    pending_request: str = ""
    pending_history_length: int = -1
    resume_request: str = ""
    profile_seen: dict = field(default_factory=dict)
    history_seen: int = 0

    def clear(self):
        self.tools = {key:"unknown" for key in TOOLS}
        self.pending_tool = self.pending_request = self.resume_request = ""
        self.profile_seen.clear()
        self.history_seen = 0
        self.pending_history_length = -1

    def reset_conversation(self):
        # Household tools persist for this session; an old 'no' must not answer a new question.
        self.pending_tool = self.pending_request = self.resume_request = ""
        self.history_seen = 0
        self.pending_history_length = -1

    def summary(self):
        return {"tools":dict(self.tools), "pending_tool":self.pending_tool,
                "resume_request":self.resume_request}

    def _read(self, text, inventory=False):
        text = norm(text)
        for clause in re.split(r"[.;,\n]|\bbut\b", text):
            if not clause.strip(): continue
            for tool,(alias,_) in TOOLS.items():
                match = re.search(r"\b(?:"+alias+r")\b", clause)
                if not match: continue
                before,after = clause[:match.start()],clause[match.end():]
                # Only user declarations, never a proposed tool or a model assertion.
                if re.search(UNKNOWN,clause) or "?" in clause:
                    continue
                negative_prefix = NEG+r"\s+(?:(?:a|an|the|our|my)\s+)?(?:(?:"+ALL_NAMES+r")\s+(?:and|or)\s+)*$"
                if re.search(negative_prefix,before) or re.search(r"^\s*(?:is |isn't |is not )?(?:broken|unavailable|not available|not working)\b",after):
                    self.tools[tool]="unavailable"
                elif re.search(POS+r"\s+(?:(?:a|an|the|our|my)\s+)?(?:(?:"+ALL_NAMES+r")\s+(?:and|or)\s+)*$",before) or re.search(r"^\s*(?:is )?(?:available|working|works)\b",after):
                    self.tools[tool]="available"
                elif inventory and not re.search(r"\b(?:need|buy|purchase|want|wish|missing|requires?|required|recommended)\b",clause):
                    self.tools[tool]="available"
            # 'Microwave only' constrains appliances, not safety tools such as thermometers.
            if re.search(r"\b(?:microwave|stove(?:top)?|oven) only\b|\bonly (?:have |have a |a )?(?:microwave|stove|oven)\b",clause):
                named={k for k in APPLIANCES if re.search(r"\b(?:"+TOOLS[k][0]+r")\b",clause)}
                for key in APPLIANCES:
                    self.tools[key]="available" if key in named else "unavailable"

    def _user(self,text,allow_short=False):
        answer=norm(text).strip(".! ")
        pending=self.pending_tool
        if pending and allow_short and answer in {"yes","yes i do","yes we do","i do","we do","no","no i don't","no we don't","i don't","we don't"}:
            self.tools[pending]="unavailable" if answer.startswith("no") or "don't" in answer else "available"
        self._read(text)
        if pending and self.tools[pending]!="unknown":
            self.resume_request=self.pending_request
            self.pending_tool=self.pending_request=""

    def observe(self,profile,history,message):
        self.resume_request = ""
        for key,value in profile.items():
            if self.profile_seen.get(key)!=value:
                self._read(value,inventory=key=="constraints")
        self.profile_seen=dict(profile)
        users=[h["content"] for h in history if h.get("role")=="user"]
        for text in users[self.history_seen:]:
            self._user(text)
        self.history_seen=len(users)
        self._user(message, allow_short=len(history)==self.pending_history_length)
        # The current user turn is appended by the caller after a successful reply.
        self.history_seen+=1

    def check(self,profile,history,message,text):
        practical = practical_check(profile,history,message,text)
        if practical:
            return practical
        required=required_tools(profile,history,message,text)
        absent=next((tool for tool in required if self.tools[tool]=="unavailable"),None)
        if absent:
            return ContextDecision(adapt_without(absent,profile),"tool:"+absent+":unavailable")
        unknown=next((tool for tool in required if self.tools[tool]=="unknown"),None)
        if unknown:
            label=TOOLS[unknown][1]
            if self.pending_tool==unknown:
                self.pending_history_length=len(history)+2
                return ContextDecision("That step still depends on an unconfirmed "+label+
                    ". We can work on parts of your meal that do not need it.", "tool:"+unknown+":pending")
            self.pending_tool=unknown
            self.pending_request=self.resume_request or message
            self.pending_history_length=len(history)+2
            return ContextDecision("Do you have a "+label+" available for this meal?", "tool:"+unknown+":unknown")
        for tool in required:
            alias,label=TOOLS[tool]
            if self.tools[tool]=="available" and re.search(r"\bdo you (?:have|own)\b[^?.]{0,25}\b(?:"+alias+r")\b",norm(text)):
                return ContextDecision("You already told me a "+label+" is available; I'll use that information for this meal.", "tool:"+tool+":known")
        return None

def required_tools(profile,history,message,text):
    value=norm(text)
    required=[]
    if poultry_cooking(analyze(value,context(profile,history,message))):
        required.append("thermometer")
    methods={
        "thermometer":r"\bthermometer\b",
        "oven":r"\b(?:oven|bake|baking|roast|roasting|broil)\b",
        "stove":r"\b(?:stove|stovetop|hob|saute|sauté|sear|simmer|pan-fry)\b",
        "microwave":r"\bmicrowave\b",
        "blender":r"\bblender\b",
        "food_processor":r"\bfood processor\b",
        "specialty_knife":r"\b(?:mandoline|specialty knife)\b",
    }
    for tool,pattern in methods.items():
        for clause in re.split(r"[.!?;]",value):
            match=re.search(pattern,clause)
            if not match: continue
            before,after=clause[:match.start()],clause[match.end():]
            if re.search(r"(?:no|without|don't use|do not use|no need for)(?: a| an| the)?\s*$",before) or re.search(r"^\s*(?:is )?(?:unavailable|not needed|not available)",after):
                continue
            if tool not in required: required.append(tool)
    return required

def adapt_without(tool,profile):
    label=TOOLS[tool][1]
    ingredients=norm(profile.get("ingredients",""))
    if tool=="thermometer":
        base="Without a food thermometer, I can't guide you to treat raw poultry as safely cooked; time and appearance cannot replace that check. "
    else:
        base="That method needs a "+label+", which you said is unavailable. "
    if re.search(r"\brice\b",ingredients):
        return base+"We can keep your familiar meal's flavors and focus on the rice and suitable seasonings you already listed. Tell me which part you want help with next."
    return base+"We can keep your familiar flavors and focus on a component using your listed ingredients and available tools, without an extra purchase."

def practical_check(profile,history,message,text):
    supplied=context(profile,history,message)
    value=norm(text)
    no_purchase=bool(re.search(r"\b(?:no (?:additional |extra )?(?:grocery |groceries |food )?(?:purchase|purchases|shopping)|(?:can't|cannot|do not|don't) (?:buy|shop)|use only what (?:i|we) have)\b",supplied))
    if no_purchase:
        for match in re.finditer(r"\b(?:buy|purchase|shop for|pick up)\b",value):
            if not re.search(r"(?:don't|do not|no need to|without|not)\s*$",value[max(0,match.start()-25):match.start()]):
                return ContextDecision("No extra purchase is needed for our next step. We'll work with the ingredients and familiar flavors you already listed; I won't make shopping part of this plan.","budget:no-purchase")
    available=re.search(r"\b(\d+)\s*(?:minutes?|mins?)\b",norm(profile.get("constraints","")))
    if available:
        durations=[int(n) for n in re.findall(r"\b(\d+)\s*(?:minutes?|mins?)\b",value)]
        if any(n>int(available.group(1)) for n in durations):
            return ContextDecision("That method exceeds the time you gave. We'll keep your meal preferences and focus on a component that fits, without shortening a required food-safety step.","time:exceeded")
    return None
