# Dependency and Runtime Record

## Approved interpreter

Existing global Python 3.11.9 at
C:\Users\GIGABYTE\AppData\Local\Programs\Python\Python311\python.exe.
Use this same installation for package management, application startup and tests.
The terminal default previously pointed elsewhere. No environment was created or
activated and no second Python was installed.

## Verified project libraries — 17 October 2026

| Library | Installed version |
| --- | --- |
| streamlit | 1.66.0 |
| google-genai | 2.31.0 |
| pydantic | 2.14.1 |
| pymupdf | 1.28.2 |
| python-docx | 1.2.0 |
| pandas | 3.0.5 |
| openpyxl | 3.1.5 |
| tabulate | 0.10.0 |
| python-dotenv | 1.2.4 |
| pytest | 9.1.1 |

The ten-library declaration remains streamlit_setup/requirements.txt. Exact
versions here record this tested machine; they are not historical pins imposed
on future working installations.

Streamlit owns the interface/state. google-genai owns provider requests. Pydantic
validates records. PyMuPDF reads selectable PDF text. python-docx reads Word.
pandas computes tabular summaries; openpyxl reads Excel cached values; tabulate
formats table previews. python-dotenv loads local configuration. pytest runs the
checks. Standard-library CSV, JSON, dates, hashes and ZIP inspection support the
new features without another package or database.

## Historical changes

On 15 October, pandas 3.0.5 was retained. Streamlit 1.66.0 and python-dotenv 1.2.4
were added for Step 1; pytest 9.1.1, iniconfig 2.3.1 and pluggy 1.7.0 were added
for Step 2. Dependency consistency passed at those stages.

## Complete-build changes — 17 October 2026

Before this build, the global dependency consistency check passed. The six missing
project libraries google-genai, pydantic, pymupdf, python-docx, openpyxl and tabulate
were previewed and installed. Each was previously absent. Their resulting versions
are in the table above.

One existing dependency required a limited change: websockets 17.2 became 16.1.1.
The installed google-genai requires websockets at least 13 and below 17; Streamlit
permits at least 12 and below 18. Version 16.1.1 satisfies both. This was a demonstrated
SDK compatibility need, not a broad downgrade. No other existing distribution
changed version. The post-installation consistency check passed.

New supporting distributions, all previously absent: annotated-types 0.8.0,
cffi 2.1.1, cryptography 50.0.2, distro 1.9.0, et-xmlfile 2.0.0,
google-auth 2.62.0, httpcore 1.0.9, httpx 0.28.1, lxml 6.1.3,
pyasn1 0.6.4, pyasn1-modules 0.4.2, pycparser 3.11,
pydantic-core 2.50.1, sniffio 1.3.1, tenacity 9.1.4 and typing-inspection 0.4.4.
The installed SDK transitive constraints express the compatible websockets range;
no extra project-level version pin was needed.

## Compatibility verification and limits

The selected interpreter imports all project modules. Readers use the tested
versions above. The local Google SDK converted the response schema without a
network call. Provider metadata/token/schema/retry behavior is tested with fake
clients, including a 60,000-millisecond timeout and SDK attempt count of one, so
application retries are not multiplied. The application's retry budget is at most
one genuinely temporary retry across the request stages.

Official SDK, structured-output and token-count references were checked during the
build. There is no configured key/model, so no live account-accessible model ID,
quota, free-tier suitability, output quality or live schema compatibility is
claimed. Configure and verify those before relying on real generation. See
PROGRESS and KNOWN_LIMITATIONS under docs for verification boundaries.

## Provider routing and local configuration

The user requested Gemini 3.6 Flash as primary, Groq openai/gpt-oss-120b as direct
fallback, and Gemini 3.8 Flash as reserve. Only explicit generation actions can
traverse that finite chain. Both key fields are private local environment values.
No new SDK or package was required for Groq; Python's standard-library HTTPS client
is used. Existing installed package versions are unchanged by this feature.
Groq's official structured-output, model and error documentation was checked.
The primary Gemini retry allowance remains one; the reserve has zero and Groq
has no automatic retry. PROGRESS.md records current local/live checks.
