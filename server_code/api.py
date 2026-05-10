import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from dataclasses import dataclass
from datetime import datetime
import secrets

# / ---- cli ---- /

# DO NOT WRITE HTTP ENDPOINTS WITHOUT KNOWING WHAT YOUR DOING!!! https://anvil.works/docs/external-resources/http-apis

# unfortunatley, authenticate_users doesnt work since we are logging in with google
# @anvil.server.http_endpoint("/ping/:content", authenticate_users=True) 
# def ping(content=None):
#   if content is None:
#     content = "ping"
#   return anvil.server.HttpResponse(200, content)

def _token_is_expired(created_at, lifetime):
  if not created_at:
    True
  return (datetime.utcnow() - created_at) > datetime.timedelta(minutes=lifetime)

def _delete_tokens(rows):
  for r in list(rows):
    try:
      r.delete()
    except Exception as e:
      print("token failed to delete", repr(e))
  
@anvil.server.callable
def verify_token(token: str) -> dict:
  try:
    if not token:
      return {"success": False, "code": 401, "message": "missing token"}

    token = app

  except

#   auth_tok = auth_tok[0]
#   created_at = auth_tok['created_at']
#   lifetime = auth_tok['lifetime']

#   expired = (
#     datetime.utcnow() - created_at
#   ) > datetime.timedelta(minutes=lifetime)
#   if expired:
#     return token_status(False, 401, "expired")

#   return token_status(True, 202, "ok")

# @anvil.server.http_endpoint("/ping/:content/:token")
# def ping(content=None, token=None, **k):
#   token_response = verify_token(token)
#   if not token_response.success:
#     return anvil.server.HttpResponse(status=token_response.code, body=f"{token_response.code}  {token_response.message}")
#   if content is None:
#     content = "ping"
#   return anvil.server.HttpResponse(status=200, body=content)

# @anvil.server.callable
# def create_cli_token(user, lifetime=10):
#   token = secrets.token_hex(32)
#   app_tables.tokens.add_row(token=token, user=user, created_at=datetime.utcnow(), lifetime=lifetime)
#   return token

# @anvil.server.http_endpoint("/get_user/by_username/:username/:token")
# def get_user(username):
#   user_to_ret
#   if user_to_return is None:
#     return anvil.server.HttpResponse(404, "404: user not found")

#   return anvil.server.HttpResponse(
#     status=200,
#     body={
#       "code": 200,
#       "data": {"username": username, "ok": "ok"}
#     })
