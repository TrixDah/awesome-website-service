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
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Args = Args::parse();

    let client: Client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
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
        "https://awesomewebsiteservice.anvil.app/_/api/{}/{}/{}",
        urlencoding::encode(&args.endpoint),
        urlencoding::encode(&args.content),
        urlencoding::encode(&args.token),
    );

    let resp = client
        .get(&url)
        .send()?;

    let status: reqwest::StatusCode = resp.status();
    let body: String = resp.text()?;

    println!("http status: {}", status);
    println!("response: {}", body);

    return Ok(());
}