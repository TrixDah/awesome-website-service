use reqwest::blocking::Client;
use serde::Deserialize;
use clap::Parser;

#[derive(Parser)]
struct Args {
    query: String,
}

#[derive(Debug, Deserialize)]
struct ApiResponse {
    code: u16,
    data: UserData,
}

#[derive(Debug, Deserialize)]
struct UserData {
    username: String,
    email: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> { 
    let args: Args = Args::parse();

    let client: Client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?; 

    let url = format!(
        "https://awesomewebsiteservice.anvil.app//_/api/get_user/by_username/{}",
        urlencoding::encode(&args.query)
    );

    let resp = client
        .get(&url)
        .send()?
        .error_for_status()?; // fails on 4xx/5xx 

    let api_response: ApiResponse = resp.json()?;

    println!("status code: {}", api_response.code);
    println!("username: {}", api_response.data.username);
    println!("email: {}", api_response.data.email);

    Ok(())
}