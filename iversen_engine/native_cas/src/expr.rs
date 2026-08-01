// Ce fichier définit la structure de données centrale : comment on représente
// une expression mathématique en mémoire, et comment on la dérive.
//
// Idée simple : une expression est soit un cas de base (un nombre, ou la
// variable x), soit une combinaison d'expressions plus petites (une somme, un
// produit...). C'est une structure récursive : une "Sum" contient une liste
// d'expressions qui peuvent elles-mêmes être des "Sum" ou des "Product", etc.

use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum Expr {
    Number(f64),                  // une constante, ex: 2.0
    Variable,                     // la variable x
    Sum(Vec<Expr>),               // une somme de plusieurs termes, ex: x + 2
    Product(Box<Expr>, Box<Expr>), // un produit de deux expressions, ex: 3 * x
    Divide(Box<Expr>, Box<Expr>), // un quotient, ex: 1 / x
    Power(Box<Expr>, i32),        // une expression élevée à une puissance entière, ex: x^3
    Function(FunctionName, Box<Expr>), // une fonction appliquée à une expression, ex: sin(x)
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum FunctionName {
    Sin,
    Cos,
    Exp,
    Ln,
}

impl FunctionName {
    fn eval(&self, x: f64) -> f64 {
        match self {
            FunctionName::Sin => x.sin(),
            FunctionName::Cos => x.cos(),
            FunctionName::Exp => x.exp(),
            FunctionName::Ln => x.ln(),
        }
    }

    fn name(&self) -> &'static str {
        match self {
            FunctionName::Sin => "sin",
            FunctionName::Cos => "cos",
            FunctionName::Exp => "exp",
            FunctionName::Ln => "ln",
        }
    }
}

impl Expr {
    /// Vérifie qu'une expression déjà simplifiée ne contient pas de cas
    /// mathématiquement indéfini connu à l'avance (ex: division par zéro
    /// écrite en dur, ln d'un nombre négatif ou nul écrit en dur).
    ///
    /// Limite assumée : cette vérification ne peut détecter que les cas où
    /// le problème est visible sans connaître x (ex: "3/0" ou "ln(-2)").
    /// Elle ne peut pas prédire qu'un "1/x" posera problème en x=0 : ça,
    /// seule l'évaluation numérique au moment voulu peut le savoir (et elle
    /// suit alors la convention standard IEEE-754 : 1.0/0.0 = infini plutôt
    /// qu'un plantage — documenté dans le README, pas un bug).
    pub fn validate(&self) -> Result<(), String> {
        match self {
            Expr::Number(_) | Expr::Variable => Ok(()),
            Expr::Sum(terms) => {
                for t in terms {
                    t.validate()?;
                }
                Ok(())
            }
            Expr::Product(a, b) => {
                a.validate()?;
                b.validate()?;
                Ok(())
            }
            Expr::Divide(a, b) => {
                a.validate()?;
                b.validate()?;
                if let Expr::Number(n) = **b {
                    if n == 0.0 {
                        return Err(format!(
                            "Division par zéro : « {} » n'est pas défini (le dénominateur vaut 0).",
                            self
                        ));
                    }
                }
                Ok(())
            }
            Expr::Power(base, _) => base.validate(),
            Expr::Function(FunctionName::Ln, inner) => {
                inner.validate()?;
                if let Expr::Number(n) = **inner {
                    if n <= 0.0 {
                        return Err(format!(
                            "ln n'est pas défini pour les nombres négatifs ou nuls : « {} » (ln de {}).",
                            self, n
                        ));
                    }
                }
                Ok(())
            }
            Expr::Function(_, inner) => inner.validate(),
        }
    }

    /// Calcule la dérivée de l'expression par rapport à x, en appliquant les
    /// règles de dérivation classiques (règle de la somme, du produit, de la
    /// puissance). C'est le cœur du moteur.
    pub fn derivative(&self) -> Expr {
        match self {
            // La dérivée d'une constante est 0.
            Expr::Number(_) => Expr::Number(0.0),

            // La dérivée de x est 1.
            Expr::Variable => Expr::Number(1.0),

            // La dérivée d'une somme est la somme des dérivées : (u+v)' = u'+v'
            Expr::Sum(terms) => {
                let derived: Vec<Expr> = terms.iter().map(|t| t.derivative()).collect();
                Expr::Sum(derived).simplify()
            }

            // Règle du produit : (u*v)' = u'*v + u*v'
            Expr::Product(u, v) => {
                let term1 = Expr::Product(Box::new(u.derivative()), v.clone());
                let term2 = Expr::Product(u.clone(), Box::new(v.derivative()));
                Expr::Sum(vec![term1, term2]).simplify()
            }

            // Règle du quotient : (u/v)' = (u'v - uv') / v^2
            Expr::Divide(u, v) => {
                let numerator = Expr::Sum(vec![
                    Expr::Product(Box::new(u.derivative()), v.clone()),
                    Expr::Product(
                        Box::new(Expr::Number(-1.0)),
                        Box::new(Expr::Product(u.clone(), Box::new(v.derivative()))),
                    ),
                ]);
                let denominator = Expr::Power(v.clone(), 2);
                Expr::Divide(Box::new(numerator.simplify()), Box::new(denominator))
            }

            // Règle de la puissance : (x^n)' = n * x^(n-1)
            // (valable ici seulement quand la base est x elle-même, cas le plus
            // courant ; le cas général avec une base composée viendra plus tard)
            Expr::Power(base, n) => {
                if **base == Expr::Variable {
                    let coefficient = Expr::Number(*n as f64);
                    if *n - 1 == 0 {
                        coefficient
                    } else if *n - 1 == 1 {
                        Expr::Product(Box::new(coefficient), Box::new(Expr::Variable)).simplify()
                    } else {
                        Expr::Product(
                            Box::new(coefficient),
                            Box::new(Expr::Power(Box::new(Expr::Variable), n - 1)),
                        )
                        .simplify()
                    }
                } else {
                    // cas général non géré pour l'instant : on le signale
                    // clairement plutôt que de renvoyer un résultat faux
                    panic!("Dérivée non implémentée pour une puissance d'une expression composée");
                }
            }

            // Règle de la chaîne : (f(g(x)))' = f'(g(x)) * g'(x)
            Expr::Function(name, inner) => {
                let outer_derivative = match name {
                    FunctionName::Sin => {
                        Expr::Function(FunctionName::Cos, inner.clone())
                    }
                    FunctionName::Cos => Expr::Product(
                        Box::new(Expr::Number(-1.0)),
                        Box::new(Expr::Function(FunctionName::Sin, inner.clone())),
                    ),
                    FunctionName::Exp => Expr::Function(FunctionName::Exp, inner.clone()),
                    FunctionName::Ln => Expr::Divide(Box::new(Expr::Number(1.0)), inner.clone()),
                };
                Expr::Product(Box::new(outer_derivative), Box::new(inner.derivative())).simplify()
            }
        }
    }

    /// Simplifie une expression : additionne les constantes entre elles,
    /// retire les termes nuls, etc. Pas une simplification complète (ce n'est
    /// pas l'objectif de cette première brique), mais assez pour que les
    /// résultats affichés soient lisibles plutôt que bruts.
    pub fn simplify(&self) -> Expr {
        match self {
            Expr::Sum(terms) => {
                let mut constant_sum = 0.0;
                let mut other_terms: Vec<Expr> = Vec::new();
                for t in terms {
                    let simplified = t.simplify();
                    match simplified {
                        Expr::Number(n) => constant_sum += n,
                        other => other_terms.push(other),
                    }
                }
                if constant_sum != 0.0 {
                    other_terms.push(Expr::Number(constant_sum));
                }
                match other_terms.len() {
                    0 => Expr::Number(0.0),
                    1 => other_terms.into_iter().next().unwrap(),
                    _ => Expr::Sum(other_terms),
                }
            }
            Expr::Product(a, b) => {
                let a = a.simplify();
                let b = b.simplify();
                match (&a, &b) {
                    (Expr::Number(x), _) if *x == 0.0 => Expr::Number(0.0),
                    (_, Expr::Number(x)) if *x == 0.0 => Expr::Number(0.0),
                    (Expr::Number(x), _) if *x == 1.0 => b,
                    (_, Expr::Number(x)) if *x == 1.0 => a,
                    (Expr::Number(x), Expr::Number(y)) => Expr::Number(x * y),
                    // fusionne les constantes imbriquées : ex. -1 * (3 * x) -> -3 * x
                    // (évite l'affichage moche "-1*3*x" tout en gardant le même résultat)
                    (Expr::Number(x), Expr::Product(inner_a, inner_b)) => {
                        if let Expr::Number(y) = **inner_a {
                            Expr::Product(Box::new(Expr::Number(x * y)), inner_b.clone()).simplify()
                        } else if let Expr::Number(y) = **inner_b {
                            Expr::Product(Box::new(Expr::Number(x * y)), inner_a.clone()).simplify()
                        } else {
                            Expr::Product(Box::new(a), Box::new(b))
                        }
                    }
                    (Expr::Product(inner_a, inner_b), Expr::Number(y)) => {
                        if let Expr::Number(x) = **inner_a {
                            Expr::Product(Box::new(Expr::Number(x * y)), inner_b.clone()).simplify()
                        } else if let Expr::Number(x) = **inner_b {
                            Expr::Product(Box::new(Expr::Number(x * y)), inner_a.clone()).simplify()
                        } else {
                            Expr::Product(Box::new(a), Box::new(b))
                        }
                    }
                    _ => Expr::Product(Box::new(a), Box::new(b)),
                }
            }
            Expr::Divide(a, b) => {
                let a = a.simplify();
                let b = b.simplify();
                match (&a, &b) {
                    (Expr::Number(x), _) if *x == 0.0 => Expr::Number(0.0),
                    (Expr::Number(x), Expr::Number(y)) if *y != 0.0 => Expr::Number(x / y),
                    (_, Expr::Number(y)) if *y == 1.0 => a,
                    _ => Expr::Divide(Box::new(a), Box::new(b)),
                }
            }
            Expr::Function(name, inner) => Expr::Function(*name, Box::new(inner.simplify())),
            other => other.clone(),
        }
    }
}

// Détecte si un terme est "négatif" (un nombre négatif, ou un produit dont le
// premier facteur numérique est négatif), et renvoie sa version affichée sans
// le signe — pour permettre à Sum de choisir entre " + " et " - ".
fn negative_form(e: &Expr) -> (bool, String) {
    match e {
        Expr::Number(n) if *n < 0.0 => (true, format_number(-n)),
        Expr::Product(a, b) => {
            if let Expr::Number(n) = **a {
                if n < 0.0 {
                    let coeff = -n;
                    let printed = if coeff == 1.0 {
                        b.to_string()
                    } else {
                        Expr::Product(Box::new(Expr::Number(coeff)), b.clone()).to_string()
                    };
                    return (true, printed);
                }
            }
            (false, e.to_string())
        }
        _ => (false, e.to_string()),
    }
}

// Une "Sum" affichée telle quelle (ex: "x + 1") redevient ambiguë si on
// l'écrit sans parenthèses à côté d'une multiplication ou d'une puissance :
// "x + 1^2" ne veut pas dire la même chose que "(x + 1)^2". Ces deux
// fonctions ajoutent des parenthèses quand c'est nécessaire pour que le
// texte affiché reste mathématiquement correct, pas seulement le calcul.
fn format_as_factor(e: &Expr) -> String {
    match e {
        Expr::Sum(_) => format!("({})", e),
        other => other.to_string(),
    }
}

fn format_as_power_base(e: &Expr) -> String {
    match e {
        Expr::Sum(_) | Expr::Product(_, _) | Expr::Divide(_, _) => format!("({})", e),
        other => other.to_string(),
    }
}

fn format_number(n: f64) -> String {
    if n.fract() == 0.0 {
        format!("{}", n as i64)
    } else {
        format!("{}", n)
    }
}


impl fmt::Display for Expr {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Expr::Number(n) => {
                if n.fract() == 0.0 {
                    write!(f, "{}", *n as i64)
                } else {
                    write!(f, "{}", n)
                }
            }
            Expr::Variable => write!(f, "x"),
            Expr::Sum(terms) => {
                let mut result = String::new();
                for (i, t) in terms.iter().enumerate() {
                    let (is_negative, printed) = negative_form(t);
                    if i == 0 {
                        if is_negative {
                            result.push('-');
                        }
                        result.push_str(&printed);
                    } else if is_negative {
                        result.push_str(" - ");
                        result.push_str(&printed);
                    } else {
                        result.push_str(" + ");
                        result.push_str(&printed);
                    }
                }
                write!(f, "{}", result)
            }
            Expr::Product(a, b) => write!(f, "{}*{}", format_as_factor(a), format_as_factor(b)),
            Expr::Divide(a, b) => write!(f, "({})/({})", a, b),
            Expr::Power(base, n) => write!(f, "{}^{}", format_as_power_base(base), n),
            Expr::Function(name, inner) => write!(f, "{}({})", name.name(), inner),
        }
    }
}

/// Évalue numériquement une expression en un point x donné.
/// (Utilisée par les tests ; conservée publique pour être réutilisable si le
/// programme principal a besoin d'évaluer une expression plus tard.)
#[allow(dead_code)]
pub fn evaluate(e: &Expr, x: f64) -> f64 {
    match e {
        Expr::Number(n) => *n,
        Expr::Variable => x,
        Expr::Sum(terms) => terms.iter().map(|t| evaluate(t, x)).sum(),
        Expr::Product(a, b) => evaluate(a, x) * evaluate(b, x),
        Expr::Divide(a, b) => evaluate(a, x) / evaluate(b, x),
        Expr::Power(base, n) => evaluate(base, x).powi(*n),
        Expr::Function(name, inner) => name.eval(evaluate(inner, x)),
    }
}

// --- Tests automatisés : mêmes exigences que le reste du projet (SymPy côté
// Python) — on vérifie des résultats connus, pas juste "ça compile". ---
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn derivative_of_constant_is_zero() {
        let f = Expr::Number(5.0);
        assert_eq!(f.derivative(), Expr::Number(0.0));
    }

    #[test]
    fn derivative_of_x_is_one() {
        let f = Expr::Variable;
        assert_eq!(f.derivative(), Expr::Number(1.0));
    }

    #[test]
    fn derivative_of_x_cubed_is_3x_squared() {
        // (x^3)' = 3x^2
        let f = Expr::Power(Box::new(Expr::Variable), 3);
        let expected = Expr::Product(Box::new(Expr::Number(3.0)), Box::new(Expr::Power(Box::new(Expr::Variable), 2)));
        assert_eq!(f.derivative(), expected);
    }

    #[test]
    fn derivative_matches_the_reference_example_from_the_python_engine() {
        // Exactement le même exemple utilisé partout ailleurs dans ce projet
        // (Python/SymPy) : f(x) = x^3 - 3x + 2, f'(x) = 3x^2 - 3.
        // On vérifie ici que le moteur Rust retombe sur le même résultat.
        let x_cubed = Expr::Power(Box::new(Expr::Variable), 3);
        let minus_three_x = Expr::Product(Box::new(Expr::Number(-3.0)), Box::new(Expr::Variable));
        let two = Expr::Number(2.0);
        let f = Expr::Sum(vec![x_cubed, minus_three_x, two]);

        let derivative = f.derivative();

        // on vérifie le résultat en l'évaluant numériquement en plusieurs
        // points plutôt qu'en comparant la structure exacte (plus robuste
        // face à l'ordre des termes) : 3x^2 - 3 doit valoir 0 en x=1 et x=-1,
        // et 9 en x=2.
        assert_eq!(evaluate(&derivative, 1.0), 0.0);
        assert_eq!(evaluate(&derivative, -1.0), 0.0);
        assert_eq!(evaluate(&derivative, 2.0), 9.0);
    }

    #[test]
    fn product_rule_is_correct() {
        // (x * x)' doit valoir 2x, donc évalué en x=5 -> 10
        let f = Expr::Product(Box::new(Expr::Variable), Box::new(Expr::Variable));
        let derivative = f.derivative();
        assert_eq!(evaluate(&derivative, 5.0), 10.0);
    }

    #[test]
    fn power_of_a_sum_keeps_parentheses_in_display() {
        // Régression : Power(Sum([x, 1]), 2) s'affichait "x + 1^2" (faux,
        // se lit comme x + (1^2)) au lieu de "(x + 1)^2". Le calcul via
        // evaluate() était déjà correct ; seul l'affichage était trompeur.
        let f = Expr::Power(
            Box::new(Expr::Sum(vec![Expr::Variable, Expr::Number(1.0)])),
            2,
        );
        assert_eq!(f.to_string(), "(x + 1)^2");
        assert_eq!(evaluate(&f, 3.0), 16.0); // (3+1)^2 = 16
    }

    #[test]
    fn product_of_a_sum_keeps_parentheses_in_display() {
        // Même famille de bug : Product(x, Sum([x, 1])) s'affichait
        // "x*x + 1" au lieu de "x*(x + 1)".
        let f = Expr::Product(
            Box::new(Expr::Variable),
            Box::new(Expr::Sum(vec![Expr::Variable, Expr::Number(1.0)])),
        );
        assert_eq!(f.to_string(), "x*(x + 1)");
    }

    #[test]
    fn simplify_removes_zero_terms() {
        let f = Expr::Sum(vec![Expr::Variable, Expr::Number(0.0)]);
        assert_eq!(f.simplify(), Expr::Variable);
    }
}
