import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import secrets

# DO NOT WRITE HTTP ENDPOINTS WITHOUT KNOWING WHAT YOUR DOING!!! https://anvil.works/docs/external-resources/http-apis

# unfortunatley, authenticate_users doesnt work since we are logging in with google
# @anvil.server.http_endpoint("/ping/:content", authenticate_users=True) 
# def ping(content=None):
#   if content is None:
#     content = "ping"
#   return anvil.server.HttpResponse(200, content)

@anvil.server.callable
def create_token(owner, lifetime=10):
    try:
        token_hex = secrets.token_hex(32)
        app_tables.tokens.add_row(token=token_hex, created_at=datetime.utcnow(), user=owner, lifetime=lifetime, revoked=False)
        return token_hex

    except Exception as e:
        print("an error occured whilst creating the token", repr(e))

def _token_is_expired(created_at, lifetime):
  if not created_at:
    return True

  return (
    datetime.now(timezone.utc) - created_at
  ) > timedelta(minutes=lifetime)

def _delete_tokens(rows):
    print("DUPED TOKEN DETECTED! DELETING")
    for r in list(rows):
        try:
            r.delete()
        except Exception as e:
            print("token failed to delete", repr(e))
  
@anvil.server.callable
def _verify_token(token: str) -> dict:
  try:
    if not token:
      return {"success": False, "code": 401, "message": "401 Unauthorized missing token"}

    token_returns = list(app_tables.tokens.search(token=token))

    if len(token_returns) == 0:
      return {"success": False, "code": 401, "message": "invalid token"}

    if len(token_returns) > 1:
      _delete_tokens(token_returns)
      return {"success": False, "code": 401, "message": "duplicate token detected"}

    token_row = token_returns[0]

    created_at = token_row['created_at']
    lifetime = token_row['lifetime']
    revoked = token_row['revoked']

    if revoked:
      return {"success": False, "code": 401, "message": "revoked"}

    if _token_is_expired(created_at, lifetime):
      try:
        token.delete()
      except Exception as e:
        print("Failed deleting expired token:", repr(e))

      return {"success": False, "code": 401, "message": "expired token"}

    return {"success": True, "code": 200, "message": "ok"}      

  except Exception as e:
    print("_verify_token exception:", repr(e))
      
# ---- ENDPOINTs ----

@anvil.server.http_endpoint("/ping/:content")
def _ping(content=None, **k):
    try:
        token = anvil.server.request.headers.get("Authorization")
        print("AUTH HEADER:", token)

        result = _verify_token(token)

        if not result["success"]:
            return anvil.server.HttpResponse(
                status=result["code"],
                body=result["message"]
            )

        return anvil.server.HttpResponse(
            status=200,
            body=content or "ping"
        )

    except Exception as e:
        print("ping endpoint exception:", repr(e))
        return anvil.server.HttpResponse(
            status=500,
            body="internal server error"
        )

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
