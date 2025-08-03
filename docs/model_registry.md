# Model Registry Documentation

## Overview

The Nova Agent Model Registry provides a centralized system for managing OpenAI model aliases and ensuring only valid model IDs are sent to the OpenAI API. This prevents "invalid model" errors while allowing developers to use friendly, memorable names in their code and configuration.

## Key Features

- **Single Source of Truth**: All model mappings are defined in one place
- **Alias Support**: Use friendly names like `gpt-4o-mini` instead of raw model IDs
- **Validation**: Early error detection for unknown model aliases
- **Environment Override**: Change default models via environment variables
- **Backward Compatibility**: Legacy invalid aliases are automatically corrected

## Model Aliases

| Alias | Maps to | Description |
|-------|---------|-------------|
| `gpt-4o-mini` | `gpt-4o` | Fast, cost-effective GPT-4 model |
| `gpt-4o-vision` | `gpt-4o` | Same as gpt-4o-mini (multimodal capable) |
| `gpt-4-turbo` | `gpt-4o` | Team shorthand for gpt-4o |
| `gpt-4` | `gpt-4o` | Legacy alias for gpt-4o |
| `gpt-3.5-mini` | `gpt-3.5-turbo` | Fast GPT-3.5 model |
| `gpt-3.5` | `gpt-3.5-turbo` | Standard GPT-3.5 model |

## Usage

### Basic Usage

```python
from nova_core.model_registry import resolve

# Resolve an alias to official model ID
model_id = resolve("gpt-4o-mini")  # Returns "gpt-4o"

# Use in OpenAI calls
import openai
response = openai.ChatCompletion.create(
    model=resolve("gpt-4o-mini"),  # Will use "gpt-4o"
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Default Model

```python
from nova_core.model_registry import resolve, get_default_model

# Use default model (from NOVA_DEFAULT_MODEL env var or "gpt-4o-mini")
model_id = resolve()  # or resolve(None)

# Get default model ID directly
default_id = get_default_model()
```

### Validation

```python
from nova_core.model_registry import is_valid_alias, resolve

# Check if alias is valid
if is_valid_alias("gpt-4o-mini"):
    model_id = resolve("gpt-4o-mini")
else:
    # Handle invalid alias
    pass

# Or let resolve() handle errors
try:
    model_id = resolve("invalid-model")
except KeyError as e:
    print(f"Invalid model: {e}")
```

## Configuration

### Environment Variables

- `NOVA_DEFAULT_MODEL`: Set the default model alias (default: "gpt-4o-mini")

### Example

```bash
export NOVA_DEFAULT_MODEL="gpt-3.5-mini"
python your_script.py  # Will use gpt-3.5-turbo as default
```

## Integration with Existing Code

### OpenAI Wrapper

The `utils/openai_wrapper.py` has been updated to use the model registry:

```python
from nova_core.model_registry import resolve as resolve_model

def chat_completion(prompt: str, model: str = None, **kwargs):
    # Resolve model alias to official OpenAI model ID
    chosen = resolve_model(model) if model else DEFAULT_MODEL
    
    return openai.ChatCompletion.create(
        model=chosen,  # Always a valid OpenAI model ID
        messages=[{"role": "user", "content": prompt}],
        **kwargs
    )
```

### Model Controller

The `utils/model_controller.py` uses the registry for model selection:

```python
from nova_core.model_registry import resolve as resolve_model

def select_model(task_meta: Dict) -> Tuple[str, str]:
    # ... model selection logic ...
    
    # Resolve model alias to official OpenAI model ID
    resolved_model = resolve_model(model)
    
    return resolved_model, api_key
```

## Adding New Aliases

To add a new model alias, edit `nova_core/model_registry.py`:

```python
MODEL_MAP: Dict[str, str] = {
    # ... existing mappings ...
    "my-custom-alias": "gpt-4o",  # Add your new alias here
}
```

## Error Handling

### Unknown Alias

```python
try:
    model_id = resolve("unknown-model")
except KeyError as e:
    print(f"Error: {e}")
    # Error message includes available aliases
```

### Direct Model ID Usage

Using a direct model ID (like `gpt-4o`) will work but emit a warning:

```python
import warnings

with warnings.catch_warnings(record=True) as w:
    model_id = resolve("gpt-4o")  # Will warn but work
    assert "Prefer using a Nova alias" in str(w[0].message)
```

## Testing

Run the model registry tests:

```bash
python -m pytest tests/test_model_registry.py -v
```

## Migration Guide

### From Direct Model IDs

**Before:**
```python
openai.ChatCompletion.create(model="gpt-4o-mini", ...)
```

**After:**
```python
from nova_core.model_registry import resolve
openai.ChatCompletion.create(model=resolve("gpt-4o-mini"), ...)
```

### From Configuration Files

**Before:**
```json
{
  "model": "gpt-4o-mini-search"  // Invalid model ID
}
```

**After:**
```json
{
  "model": "gpt-4o-mini"  // Valid alias that resolves to gpt-4o
}
```

## Benefits

1. **Prevents API Errors**: No more "invalid model" errors from OpenAI
2. **Centralized Management**: All model mappings in one place
3. **Easy Updates**: Change model mappings without code changes
4. **Environment Flexibility**: Override models via environment variables
5. **Developer Friendly**: Use memorable aliases instead of raw model IDs
6. **Future Proof**: Easy to update when OpenAI changes model names

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `nova_core` is in your Python path
2. **Unknown Alias**: Check the available aliases with `get_available_aliases()`
3. **Environment Variable**: Verify `NOVA_DEFAULT_MODEL` is set correctly

### Debug Mode

```python
from nova_core.model_registry import get_available_aliases, get_official_models

print("Available aliases:", get_available_aliases())
print("Official models:", get_official_models())
``` 