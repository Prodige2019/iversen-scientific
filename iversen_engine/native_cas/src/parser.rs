// Ce fichier transforme un texte comme "x^3 - 3*x + 2" en une structure Expr
// que le reste du moteur (dérivation, évaluation) sait manipuler.
//
// Deux étapes classiques :
// 1. "tokenize" découpe le texte en petits morceaux (des "jetons") :
//    nombre, symbole x, opérateur +, -, *, /, ^, parenthèses, mots-clés de
//    fonction (sin, cos, exp, ln).
// 2. Le "Parser" relit ces jetons et reconstruit l'expression, en respectant
//    les règles de priorité habituelles (fonctions et ^ avant * et /, qui
//    sont eux-mêmes avant + et -).
//
// Portée actuelle : nombres, x, +, -, *, /, ^ (exposant entier), parenthèses,
// sin(...), cos(...), exp(...), ln(...).
//
// Note technique : le tokenizer lisait auparavant chaque lettre séparément
// (un seul caractère possible : 'x'). Pour reconnaître des mots-clés comme
// "sin", il lit maintenant des identifiants complets (suites de lettres),
// puis décide si le mot lu est "x" (la variable) ou un nom de fonction connu.

use crate::expr::Expr;
use crate::expr::FunctionName;

#[derive(Debug, Clone, PartialEq)]
enum Token {
    Number(f64),
    X,
    Plus,
    Minus,
    Star,
    Slash,
    Caret,
    LParen,
    RParen,
    Func(FunctionName),
}

fn tokenize(input: &str) -> Result<Vec<Token>, String> {
    let mut tokens = Vec::new();
    let chars: Vec<char> = input.chars().collect();
    let mut i = 0;

    while i < chars.len() {
        let c = chars[i];
        if c.is_whitespace() {
            i += 1;
        } else if c == '+' {
            tokens.push(Token::Plus);
            i += 1;
        } else if c == '-' {
            tokens.push(Token::Minus);
            i += 1;
        } else if c == '*' {
            tokens.push(Token::Star);
            i += 1;
        } else if c == '/' {
            tokens.push(Token::Slash);
            i += 1;
        } else if c == '^' {
            tokens.push(Token::Caret);
            i += 1;
        } else if c == '(' {
            tokens.push(Token::LParen);
            i += 1;
        } else if c == ')' {
            tokens.push(Token::RParen);
            i += 1;
        } else if c.is_ascii_alphabetic() {
            // Lit un mot entier (suite de lettres) : soit "x" (la variable),
            // soit un nom de fonction connu (sin, cos, exp, ln).
            let start = i;
            while i < chars.len() && chars[i].is_ascii_alphabetic() {
                i += 1;
            }
            let word: String = chars[start..i].iter().collect();
            match word.as_str() {
                "x" => tokens.push(Token::X),
                "sin" => tokens.push(Token::Func(FunctionName::Sin)),
                "cos" => tokens.push(Token::Func(FunctionName::Cos)),
                "exp" => tokens.push(Token::Func(FunctionName::Exp)),
                "ln" => tokens.push(Token::Func(FunctionName::Ln)),
                _ => {
                    return Err(format!(
                        "Mot non reconnu : « {} » (position {}). Seuls x, sin, cos, exp, ln sont supportés pour l'instant.",
                        word, start
                    ));
                }
            }
        } else if c.is_ascii_digit() || c == '.' {
            let start = i;
            while i < chars.len() && (chars[i].is_ascii_digit() || chars[i] == '.') {
                i += 1;
            }
            let number_str: String = chars[start..i].iter().collect();
            let value = number_str
                .parse::<f64>()
                .map_err(|_| format!("Nombre illisible : « {} »", number_str))?;
            tokens.push(Token::Number(value));
        } else {
            return Err(format!(
                "Caractère non reconnu : « {} » (position {}). Seuls x, +, -, *, /, ^, (, ), sin, cos, exp, ln et les nombres sont supportés pour l'instant.",
                c, i
            ));
        }
    }
    Ok(tokens)
}

struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.pos)
    }

    fn advance(&mut self) -> Option<Token> {
        let t = self.tokens.get(self.pos).cloned();
        self.pos += 1;
        t
    }

    // expression = term (('+' | '-') term)*
    fn parse_expression(&mut self) -> Result<Expr, String> {
        let mut terms = vec![self.parse_term()?];
        loop {
            match self.peek() {
                Some(Token::Plus) => {
                    self.advance();
                    terms.push(self.parse_term()?);
                }
                Some(Token::Minus) => {
                    self.advance();
                    let t = self.parse_term()?;
                    terms.push(Expr::Product(Box::new(Expr::Number(-1.0)), Box::new(t)));
                }
                _ => break,
            }
        }
        if terms.len() == 1 {
            Ok(terms.into_iter().next().unwrap())
        } else {
            Ok(Expr::Sum(terms))
        }
    }

    // term = power (('*' | '/') power)*
    // '*' et '/' ont la même priorité, appliqués de gauche à droite.
    fn parse_term(&mut self) -> Result<Expr, String> {
        let mut result = self.parse_power()?;
        loop {
            match self.peek() {
                Some(Token::Star) => {
                    self.advance();
                    let rhs = self.parse_power()?;
                    result = Expr::Product(Box::new(result), Box::new(rhs));
                }
                Some(Token::Slash) => {
                    self.advance();
                    let rhs = self.parse_power()?;
                    result = Expr::Divide(Box::new(result), Box::new(rhs));
                }
                _ => break,
            }
        }
        Ok(result)
    }

    // power = unary ('^' entier)?
    fn parse_power(&mut self) -> Result<Expr, String> {
        let base = self.parse_unary()?;
        if let Some(Token::Caret) = self.peek() {
            self.advance();
            match self.advance() {
                Some(Token::Number(n)) if n.fract() == 0.0 => {
                    Ok(Expr::Power(Box::new(base), n as i32))
                }
                other => Err(format!(
                    "Après « ^ », seul un exposant entier est supporté pour l'instant (reçu : {:?}).",
                    other
                )),
            }
        } else {
            Ok(base)
        }
    }

    // unary = '-' unary | primary
    fn parse_unary(&mut self) -> Result<Expr, String> {
        if let Some(Token::Minus) = self.peek() {
            self.advance();
            let inner = self.parse_unary()?;
            return Ok(Expr::Product(Box::new(Expr::Number(-1.0)), Box::new(inner)));
        }
        self.parse_primary()
    }

    // primary = nombre | 'x' | '(' expression ')' | nom_fonction '(' expression ')'
    fn parse_primary(&mut self) -> Result<Expr, String> {
        match self.advance() {
            Some(Token::Number(n)) => Ok(Expr::Number(n)),
            Some(Token::X) => Ok(Expr::Variable),
            Some(Token::LParen) => {
                let inner = self.parse_expression()?;
                match self.advance() {
                    Some(Token::RParen) => Ok(inner),
                    _ => Err("Parenthèse ouvrante sans parenthèse fermante correspondante.".to_string()),
                }
            }
            Some(Token::Func(name)) => {
                match self.advance() {
                    Some(Token::LParen) => {}
                    other => {
                        return Err(format!(
                            "Une fonction doit être suivie d'une parenthèse ouvrante, ex: sin(x) (reçu : {:?}).",
                            other
                        ));
                    }
                }
                let inner = self.parse_expression()?;
                match self.advance() {
                    Some(Token::RParen) => Ok(Expr::Function(name, Box::new(inner))),
                    _ => Err("Parenthèse ouvrante sans parenthèse fermante correspondante après une fonction.".to_string()),
                }
            }
            other => Err(format!("Expression inattendue (reçu : {:?}).", other)),
        }
    }
}

/// Point d'entrée public : transforme un texte en expression, ou une erreur
/// explicite (jamais de panique) si le texte est illisible.
pub fn parse(input: &str) -> Result<Expr, String> {
    let tokens = tokenize(input)?;
    if tokens.is_empty() {
        return Err("Expression vide.".to_string());
    }
    let mut parser = Parser { tokens, pos: 0 };
    let result = parser.parse_expression()?;
    if parser.pos != parser.tokens.len() {
        return Err(format!(
            "Texte inattendu après la position {} dans l'expression.",
            parser.pos
        ));
    }
    let simplified = result.simplify();
    simplified.validate()?;
    Ok(simplified)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::expr::evaluate;

    #[test]
    fn parses_the_reference_example_and_matches_python_engine() {
        // Même exemple que partout ailleurs dans ce projet.
        let f = parse("x^3 - 3*x + 2").expect("devrait se parser");
        assert_eq!(evaluate(&f, 0.0), 2.0);
        assert_eq!(evaluate(&f, 1.0), 0.0); // 1 - 3 + 2 = 0
        assert_eq!(evaluate(&f, 2.0), 4.0); // 8 - 6 + 2 = 4
    }

    #[test]
    fn parses_and_derives_correctly() {
        let f = parse("x^2").expect("devrait se parser");
        let d = f.derivative();
        assert_eq!(evaluate(&d, 5.0), 10.0); // (x^2)' = 2x, en x=5 -> 10
    }

    #[test]
    fn handles_parentheses() {
        let f = parse("2*(x + 1)").expect("devrait se parser");
        assert_eq!(evaluate(&f, 3.0), 8.0); // 2*(3+1) = 8
    }

    #[test]
    fn handles_unary_minus() {
        let f = parse("-x + 5").expect("devrait se parser");
        assert_eq!(evaluate(&f, 2.0), 3.0); // -2 + 5 = 3
    }

    #[test]
    fn rejects_unknown_characters_with_clear_error() {
        let result = parse("x^3 & 2");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("non reconnu"));
    }

    #[test]
    fn rejects_unbalanced_parentheses() {
        let result = parse("(x + 1");
        assert!(result.is_err());
    }

    #[test]
    fn rejects_non_integer_exponent_explicitly() {
        // Limite honnête et assumée de cette première version : pas de x^0.5
        let result = parse("x^0.5");
        assert!(result.is_err());
    }

    #[test]
    fn rejects_literal_division_by_zero_with_clear_error() {
        let result = parse("1/0");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Division par zéro"));
    }

    #[test]
    fn rejects_division_by_an_expression_that_simplifies_to_zero() {
        // "2 - 2" se simplifie en 0 : doit être détecté même si ce n'est
        // pas littéralement écrit "0" au départ.
        let result = parse("3/(2 - 2)");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Division par zéro"));
    }

    #[test]
    fn rejects_ln_of_a_negative_literal() {
        let result = parse("ln(-3)");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("n'est pas défini"));
    }

    #[test]
    fn rejects_ln_of_zero() {
        let result = parse("ln(0)");
        assert!(result.is_err());
    }

    #[test]
    fn accepts_one_over_x_since_the_problem_only_appears_at_a_specific_x_value() {
        // "1/x" est une expression valide en elle-même : ce n'est qu'en
        // l'évaluant *en x=0* que ça pose problème, ce qu'on ne peut pas
        // savoir avant. C'est un cas différent de "1/0" (littéralement
        // indéfini quel que soit x).
        let result = parse("1/x");
        assert!(result.is_ok());
    }

    #[test]
    fn evaluating_one_over_x_at_zero_follows_ieee754_convention_not_a_crash() {
        // Comportement documenté (README), pas un plantage silencieux :
        // en Rust/IEEE-754, division d'un flottant non-nul par zéro donne
        // l'infini plutôt que de planter. On verrouille ce comportement
        // explicitement pour qu'il reste intentionnel, pas un oubli.
        let f = parse("1/x").expect("devrait se parser");
        assert_eq!(evaluate(&f, 0.0), f64::INFINITY);
    }

    #[test]
    fn parses_division_and_evaluates_correctly() {
        let f = parse("x/2").expect("devrait se parser");
        assert_eq!(evaluate(&f, 10.0), 5.0);
    }

    #[test]
    fn derivative_of_one_over_x_is_minus_one_over_x_squared() {
        // (1/x)' = -1/x^2
        let f = parse("1/x").expect("devrait se parser");
        let d = f.derivative();
        for point in [1.0, 2.0, 5.0, -3.0] {
            let expected = -1.0 / (point * point);
            assert!(
                (evaluate(&d, point) - expected).abs() < 1e-9,
                "en x={}, attendu {} mais obtenu {}",
                point,
                expected,
                evaluate(&d, point)
            );
        }
    }

    #[test]
    fn derivative_of_sin_is_cos() {
        let f = parse("sin(x)").expect("devrait se parser");
        let d = f.derivative();
        for point in [0.0f64, 1.0, 2.0, -1.5] {
            let expected = point.cos();
            assert!((evaluate(&d, point) - expected).abs() < 1e-9);
        }
    }

    #[test]
    fn derivative_of_cos_is_minus_sin() {
        let f = parse("cos(x)").expect("devrait se parser");
        let d = f.derivative();
        for point in [0.0f64, 1.0, 2.0, -1.5] {
            let expected = -point.sin();
            assert!((evaluate(&d, point) - expected).abs() < 1e-9);
        }
    }

    #[test]
    fn derivative_of_exp_is_itself() {
        let f = parse("exp(x)").expect("devrait se parser");
        let d = f.derivative();
        for point in [0.0f64, 1.0, 2.0, -1.0] {
            let expected = point.exp();
            assert!((evaluate(&d, point) - expected).abs() < 1e-9);
        }
    }

    #[test]
    fn derivative_of_ln_is_one_over_x() {
        let f = parse("ln(x)").expect("devrait se parser");
        let d = f.derivative();
        for point in [1.0, 2.0, 5.0, 0.1] {
            let expected = 1.0 / point;
            assert!((evaluate(&d, point) - expected).abs() < 1e-9);
        }
    }

    #[test]
    fn parses_nested_function_call_with_chain_rule() {
        // (sin(2*x))' = cos(2*x) * 2
        let f = parse("sin(2*x)").expect("devrait se parser");
        let d = f.derivative();
        for point in [0.0f64, 1.0, 3.0] {
            let expected = (2.0 * point).cos() * 2.0;
            assert!((evaluate(&d, point) - expected).abs() < 1e-9);
        }
    }

    #[test]
    fn function_name_still_rejects_unknown_word() {
        let result = parse("tan(x)");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("non reconnu"));
    }

    #[test]
    fn leading_negative_term_keeps_its_sign_in_display() {
        // Régression : "-x + 5" s'affichait auparavant "x + 5" (signe perdu
        // sur le tout premier terme d'une somme) — le calcul était correct,
        // seul l'affichage était faux. On verrouille ici le texte affiché,
        // pas seulement le résultat numérique.
        let f = parse("-x + 5").expect("devrait se parser");
        assert_eq!(f.to_string(), "-x + 5");
    }
}
