mod expr;
mod parser;

use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();

    let input = if args.len() >= 2 {
        args[1..].join(" ")
    } else {
        // valeur par défaut si aucun texte n'est fourni : le même exemple
        // utilisé partout ailleurs dans ce projet
        "x^3 - 3*x + 2".to_string()
    };

    match parser::parse(&input) {
        Ok(f) => {
            println!("f(x)  = {}", f);
            println!("f'(x) = {}", f.derivative());
        }
        Err(e) => {
            eprintln!("Erreur : {}", e);
            std::process::exit(1);
        }
    }
}
