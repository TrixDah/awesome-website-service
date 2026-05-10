# Endpoints

## Creating endpoints signatures

an endpoint is defined with the decorator:
```python
@anvil.server.http_endpoint(path: str)
```

paths can be plain
```python
@anvil.server.http_endpoint("/ping")
```

or they can take fields
```python
@anvil.server.http_endpoint("/get_user/by_username/:username/:token")
```

every endpoint that you make **MUST** include a `:token` param at the end (by convention) in order to make sure the db stays secure.

a function signature for a endpoint may look like this

```python
@anvil.server.http_endpoint("/ping/:content/:token")
def ping(content=None, token=None, **k):
```

content and token automatically get taken from `:content` and `:token` and anything after `?field=...` is filled into the kwargs dict. 

## writing endpoint bodies

endpoint function bodies must be wrapped in a try except block to ensure logs are made properly.

```python
try:
  ...
except Exception as e:
  print("<source> exception:", repr(e))
  return anvil.server.HttpResponse(
    status=500,
    body="internal server error"
  )
```

endpoints should return the object that they are trying to pass. they must be wrapped in `anvil.server.HttpResponse` objects so the browser and the CLI can understand them.
headers can be included but it is not a requirement

a succesful operation may look like this

```python
return anvil.server.HttpResponse(
  status=200,
  body=content or "ping"
)
```

the body is what the browser will see and what the CLI will get so make sure its formatted consistently

endpoint bodies **MUST** include a check for the token against the database, whcich i will get into now.

## validating tokens

validating an API token is not exactly a one step procedure.
luckily, i have supplied a function called `validate_token` which takes in a str `token` and returns a dict which looks like this

```python
{"success": True, "code": 200, "message": "ok"}
```

the reason it is a dict and not a custome class is becuase sending custom classes over http is difficult.

validating a token in your function is as simple as putting this at the start

```python
result = verify_token(token)
    
    if not result['success']:
      return anvil.server.HttpResponse(
        status=result["code"],
        body=f'{result["code"]} {result["message"]}'
      )
```

including this check in your function body is critical and failing to do so can compromise the entire db.

## Example function

putting everything together, we can see one of the simplest http functions out there, the `ping()`
in our case, it looks something like this

```python
@anvil.server.http_endpoint("/ping/:content/:token") # endpoint handle
def ping(content=None, token=None): # binds directly from the handle
  try: # must include to ensure error propogation
    result = verify_token(token) # verify token
    
    if not result['success']:
      return anvil.server.HttpResponse(
        status=result["code"],
        body=f'{result["code"]} {result["message"]}'
      )

    # finally return a response with the supplied content, or ping
    return anvil.server.HttpResponse(
      status=200,
      body=content or "ping"
    )
    
  except Exception as e: # if an exception occurs above, this code will run
    # propogate the error `e` into the logs and return a failed response
    print("ping endpoint exception:", repr(e))
    return anvil.server.HttpResponse(
      status=500,
      body="internal server error"
    )
```

## connecting your endpoints to the CLI

WIP
