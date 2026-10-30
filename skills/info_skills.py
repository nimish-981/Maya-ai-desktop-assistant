"""
skills/info_skills.py

Knowledge & information tools: Wikipedia, jokes, calculations.
These functions are auto-registered as Groq tools via engine.py.
"""
import json


def search_wikipedia(topic: str) -> str:
    """Searches Wikipedia for a topic and returns a concise summary."""
    try:
        import wikipedia
        wikipedia.set_lang("en")
        try:
            summary = wikipedia.summary(topic, sentences=4, auto_suggest=True)
            return f"Here is what I found on Wikipedia about {topic}: {summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            # Pick the first option
            try:
                summary = wikipedia.summary(e.options[0], sentences=4)
                return f"There were multiple results. Here is information about {e.options[0]}: {summary}"
            except Exception:
                return f"Wikipedia has multiple results for '{topic}'. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"I could not find a Wikipedia page for '{topic}'. Please try a different search term."
    except ImportError:
        return "The Wikipedia library is not installed. Please run: pip install wikipedia"
    except Exception as e:
        return f"Wikipedia search error: {e}"


def get_joke() -> str:
    """Tells a random funny joke to lighten the mood."""
    try:
        import urllib.request
        url = "https://v2.jokeapi.dev/joke/Programming,Miscellaneous?blacklistFlags=nsfw,explicit&type=single"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                if data.get("type") == "single":
                    return data.get("joke", "I tried to think of a joke but my humor module crashed.")
                elif data.get("type") == "twopart":
                    return f"{data['setup']} ... {data['delivery']}"
        except Exception:
            pass
        # Fallback jokes
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
            "Why do Java developers wear glasses? Because they don't C sharp!",
            "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
            "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
        ]
        import random
        return random.choice(jokes)
    except Exception as e:
        return f"I could not fetch a joke right now: {e}"


def calculate(expression: str) -> str:
    """Safely evaluates a mathematical expression and returns the result. Example: '25 * 4 + 10'."""
    import ast
    import operator

    # Allowed operators only — no exec/eval of arbitrary code
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in ops:
                raise ValueError(f"Unsupported operator: {op_type}")
            return ops[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in ops:
                raise ValueError(f"Unsupported operator: {op_type}")
            return ops[op_type](_eval(node.operand))
        else:
            raise ValueError(f"Unsupported expression type: {type(node)}")

    try:
        # Clean the expression
        clean_expr = expression.strip().replace("^", "**")
        tree = ast.parse(clean_expr, mode='eval')
        result = _eval(tree.body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"The result of {expression} is {result}."
    except ZeroDivisionError:
        return "That expression causes a division by zero, which is undefined."
    except Exception as e:
        return f"I could not calculate '{expression}'. Please check the expression. Error: {e}"
