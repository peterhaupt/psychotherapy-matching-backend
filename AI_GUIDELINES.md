# Requirements for AI coding assistance

## Core Principles
- **READ ALL INSTRUCTIONS THOROUGHLY** before responding
- Never assume you understand requirements - verify first
- Acknowledge when you don't understand something
- Focus on exactly what is asked, no more and no less

## Work Methodology
- Proceed in small, detailed steps - never large jumps
- Ask for explicit approval before performing longer steps
- Remind me to document changes after completing sections
- Deliver one artifact at a time unless I specifically request multiple
- When asked to create files, only create exactly what was requested

## Configuration Management
- **NEVER USE HARDCODED PARAMETERS** in application code
- Always create a centralized configuration mechanism (config files, environment variables)
- Use consistent parameter naming across all files
- Provide sensible defaults but allow for overrides
- Document all configuration parameters and their purpose
- Keep sensitive information (passwords, API keys) in environment variables

## Naming Conventions

### Database and Model Fields
- **USE GERMAN NAMES FOR ALL DATABASE FIELDS** to maintain consistency with existing codebase
- Match existing patterns: `vorname`, `nachname`, `strasse`, `plz`, `ort`
- Use underscores for compound German words: `telefonische_erreichbarkeit`, `naechster_kontakt_moeglich`
- Keep technical/system fields in English: `id`, `created_at`, `updated_at`
- Model attributes must match database field names exactly (no translation layer)

### Code and Variables
- Use English for variable names, function names, and comments
- API endpoint paths can use English REST conventions
- Class names follow English Python conventions

### Examples
✅ Correct:
```python
# Model field (German)
bevorzugte_diagnosen = Column(JSONB)

# Variable name (English)
preferred_diagnoses_list = therapist.bevorzugte_diagnosen
```

❌ Incorrect:
```python
# Model field (English - wrong!)
preferred_diagnoses = Column(JSONB)

# Mixing languages in same context
bevorzugteDiagnoses = []  # Don't mix!
```

## Error Handling
- First explain an error completely - only fix after analysis is approved
- Never guess what an error might be - always properly analyze until certain
- Understanding an error is more important than fixing it
- Avoid speculative language ("might", "likely", "probably", etc.) in error analysis
- Provide definitive error analysis before any fix

## Code and Documentation
- Always provide code and markdown files as artifacts that I can copy
- Be precise with code examples - make them directly usable
- When creating bash scripts or other tools, follow instructions exactly
- Document any non-obvious code with relevant comments
- Apply consistent formatting and style throughout the codebase
- Avoid repetition of configuration values across multiple files

## Communication Style
- Ask questions if anything is unclear
- Don't assume default configurations - verify first
- Be direct and concise in explanations
- Focus on understanding issues before proposing solutions
- Warn about potential issues rather than proceeding with uncertain approaches

## System Design Principles
- Use proper abstraction layers for configuration, business logic, and data access
- Follow the principle of least surprise in API design
- Create reusable utilities for common operations
- Ensure consistent error handling patterns across modules
- Design for testability from the beginning

## Key Behaviors to Avoid
- Creating more than requested
- Assuming requirements without verification
- Proceeding to implementation before understanding is confirmed
- Offering partial solutions when complete analysis is required
- Excessive verbosity when brief responses would suffice
- Ignoring project documentation or requirements
- Duplicating configuration values across the codebase
- Using magic numbers or hardcoded strings in application code
- **Mixing German and English field names in database schemas**