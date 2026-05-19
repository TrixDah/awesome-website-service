use clap::{Parser, Subcommand};
use reqwest::blocking::Client;
use std::{error::Error, fs};
use dirs::config_dir;

#[derive(Parser)]
#[command(about = "ACLS: CLI tool for awesomewebsiteservice")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// save token
    Login {
        #[arg(short, long)]
        token: Option<String>,
    },
    /// clear saved token
    Logout,
    /// call an API endpoint
    Call {
        endpoint: String,
        content: String,
        #[arg(short, long)]
        token: Option<String>,
        #[arg(long)]
        force: bool,
        #[arg(short, long)]
        url: Option<String>,
    },
}

fn save_token(token: &str) -> Result<(), Box<dyn Error>> {
    let dir = config_dir()
        .ok_or("could not find config directory")?
        .join("ACLS");

    fs::create_dir_all(&dir)?;
    fs::write(dir.join("token"), token)?;

    Ok(())
}

fn load_token() -> Result<String, Box<dyn Error>> {
    let path = config_dir()
        .ok_or("could not find config directory")?
        .join("ACLS")
        .join("token");

    Ok(fs::read_to_string(path)?)
}

fn login(token: Option<String>) -> Result<(), Box<dyn Error>> {
    let tok = match token {
        Some(t) => t,
        None => rpassword::prompt_password("Token: ")?,
    };

    save_token(&tok)?;

    Ok(())
}

fn logout() {

}

fn call(
    endpoint: String,
    content: String,
    token: Option<String>,
    force: bool,
    url: Option<String>,
) -> Result<(), Box<dyn Error>> {
    const ENDPOINTS: &[&str] = &["ping"];

    if !ENDPOINTS.contains(&endpoint.as_str()) && !force {
        return Err(format!("invalid endpoint! endpoint {} not found", endpoint).into());
    }

    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .redirect(reqwest::redirect::Policy::none())
        .build()?;

    let url = format!(
        "{}/_/api/{}/{}",
        url.unwrap_or_else(|| "https://awesomewebsiteservice.anvil.app".to_string())
            .trim_end_matches('/'),
        endpoint,
        content
    );

    let resp = client
        .get(url)
        .header("Authorization", format!("Bearer {}", token.unwrap_or(load_token()?)))
        .send()?;

    let status = resp.status();
    let body = if status.as_u16() == 404 {
        "not found!".to_string()
    } else {
        resp.text()?
    };

    println!("http status: {}", status);
    println!("response: {}", body);

    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let cli = Cli::parse();

    match cli.command {
        Command::Login { token } => login(token)?,
        Command::Logout => logout(),
        Command::Call { endpoint, content, token, force, url } => {
            call(endpoint, content, token, force, url)?
        }
    }

    Ok(())
}