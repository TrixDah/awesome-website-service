use reqwest::blocking::Client;
use clap::Parser;

#[derive(Parser)]
struct Args {
    content: String,

    #[arg(short, long)]
    token: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    let url = format!(
        "https://awesomewebsiteservice.anvil.app/_/api/ping/{}/{}",
        urlencoding::encode(&args.content),
        urlencoding::encode(&args.token),
    );

    let resp = client
        .get(&url)
        .send()?;

    let status = resp.status();
    let body = resp.text()?;

    println!("http status: {}", status);
    println!("response: {}", body);

    Ok(())
}