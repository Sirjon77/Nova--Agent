"""Prompt generation utilities for Nova Agent."""

def generate_prompt_variants(base_prompt: str, num_variants: int = 3) -> list[str]:
    """Generate variations of a base prompt for A/B testing."""
    variants = [base_prompt]  # Always include the original
    
    # Simple variations for now - in production this would use more sophisticated techniques
    variations = [
        f"Please provide a detailed response to: {base_prompt}",
        f"Can you help me with: {base_prompt}",
        f"I need assistance with: {base_prompt}"
    ]
    
    # Add variations up to the requested number
    for i in range(min(num_variants - 1, len(variations))):
        variants.append(variations[i])
    
    return variants[:num_variants] 