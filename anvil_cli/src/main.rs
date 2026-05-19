use reqwest::blocking::Client;
use clap::Parser;
use std::error::Error;

#[derive(Parser)]
struct Args {
    content: String,

    #[arg(short, long)]
    endpoint: String,

    #[arg(short, long)]
    token: String,

    #[arg(long)]
    force: bool,

    #[arg(short, long)]
    url: Option<String>,
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Args = Args::parse();

    let client: Client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .redirect(reqwest::redirect::Policy::none())
        .build()?;

    let force: &bool = &args.force;
    let endpoint: &String = &args.endpoint;

    let endpoints: [&'static str; _] = [
        "ping",
    ];

    if !endpoints.contains(&endpoint.as_str()) && !*force {
        return Err(format!("invalid endpoint! endpoint {} not found", endpoint).into());
    }

    let url = format!(
        "{}/_/api/{}/{}",
        args.url.unwrap().trim_end_matches('/'),
        args.endpoint,
        args.content
    );

    let resp = client
        .get(url.clone())
        .header("Authorization", format!("Bearer {}", args.token))
        .send()?;

    let status: reqwest::StatusCode = resp.status();
    let mut body: String = resp.text()?;
    if status.as_u16() == 404 {
        body = String::from("not found!")
    }

    println!("http status: {}", status);
    println!("response: {}", body);

    return Ok(());
}