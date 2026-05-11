# Endpoints

## Creating endpoints signatures

an endpoint is defined with the decorator:
```python
@anvil.server.http_endpoint(path: str)
```

paths look like this
```python
@anvil.server.http_endpoint("/get_user/by_username/:username/:token")
```

paths to your endpoint can be found at `https://awesomewebsiteservice.anvil.app/_/api {path}` 

if you are testing out a new endpoint, create a new private link in anvil and delete it after your session ends. for example `https://g6rtkujpqxu3v6fy.anvil.app/QIUSVHHFP5RCEB5G41J473HL/_/api {path}`

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

## using and connecting your endpoints to the CLI

the cli is written in rust using clap.

right now the args look like this

```rust
struct Args {
    content: String,

    #[arg(short, long)]
    endpoint: String,

    #[arg(short, long)]
    token: String,

    #[arg(long)]
    force: bool,
}
```

handling the args is as simple as this

```rust
let url: String = format!(
    "https://awesomewebsiteservice.anvil.app/_/api/{}/{}/{}",
    urlencoding::encode(&args.endpoint),
    urlencoding::encode(&args.content),
    urlencoding::encode(&args.token),
);
```

right now we only have post actions so its pretty straight forward, just add your endpoint to the `endpoints: :[&'static str; _]` array or make it only accsesable only through --force by ommiting it

```rust
let endpoints: [&'static str; _] = [
        "ping",
];
```

if you want the cli to do something with the response, isolate it in its own `Result<(), Box<dyn Error>>` function

## managing API tokens

WIP

lifetime in mins
```pyton
from .api import create_token
create_token(user: str, lifetime: int)
```
