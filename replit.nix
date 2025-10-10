{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.fastapi
    pkgs.python310Packages.uvicorn
    pkgs.python310Packages.pydantic
    pkgs.python310Packages.aiofiles
    pkgs.python310Packages.requests
    pkgs.python310Packages.python-multipart
    pkgs.python310Packages.email-validator
    pkgs.python310Packages.jinja2
  ];
}
