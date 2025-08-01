from openai import OpenAI
client = OpenAI()

def should_remember(user_message: str) -> bool:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return 'yes' if the message should be stored long‑term."},
            {"role": "user", "content": user_message},
        ],
    )
    return completion.choices[0].message.content.lower().startswith("yes")
