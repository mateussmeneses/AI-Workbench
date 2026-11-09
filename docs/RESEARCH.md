# Community and ecosystem research — 30 October 2026

Research was used to guide architecture; community comments are experience reports, not independent benchmarks.

## Verified references

- [Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx): `SKILL.md` plus progressive disclosure; keep metadata compact and load details only for relevant tasks.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec): cross-agent, change-centered specification workflow; works for existing and new projects. Workbench keeps continuity and area routing without copying OpenSpec source.
- [GitHub Spec Kit](https://github.com/github/spec-kit): modular specify/plan/implement/verify workflows; inspires profile-independent lifecycle phases.
- [Reddit: skills overload](https://www.reddit.com/r/ClaudeCode/comments/1t4cy2y/what_do_you_do_when_you_have_too_much_skills/): reports of ignored/conflicting large skills, motivates opt-in per-project scope.
- [Reddit: MCP overload](https://www.reddit.com/r/ClaudeMCP/comments/1wibujg/mcp_is_great_until_you_have_too_many_servers/): reports of performance/context clutter from enabling many MCPs; motivates recommend-only MCP selection.
- [Reddit: persistent context](https://www.reddit.com/r/codex/comments/1wjaaaf/for_those_of_you_that_that_run_out_on_the_plus_do/): independent community project documents Git-derived, selectively loaded project memory; motivates private evidence-based handoffs.
- [Reddit: multi-agent board](https://www.reddit.com/r/ClaudeAI/comments/1rtiqne/a_coding_agent_session_manager_that_manages/): illustrates phase-specific agent choice and delegation rather than a single default agent for all work.
- [Reddit: tool catalog bloat](https://www.reddit.com/r/ClaudeAI/comments/1ofltdr/i_spent_way_too_long_cataloguing_claude_code/): firsthand report of pruning excessive tools and plugins; motivates bounded recommendations.

X/Twitter queries during this research did not yield sufficiently verifiable, relevant primary examples. No claims about community consensus on X are made.

## Decisions adopted

1. Use one canonical registry with 27 composable, extendable areas; do not load every skill.
2. Separate discovery from installation: `recommend` is read-only; `init` explicitly copies skills.
3. Recommend MCPs and third-party plugins but never activate/install without a separate user-authorized workflow.
4. Store private continuity in `.ai-workbench`, with Git as authoritative state.
5. Make explanations and area overrides available to users; never present heuristic scores as calibrated probabilities.
6. Avoid dependency on commercial APIs for project discovery or continuity.

## Curated references — 9 November 2026

Selected from reviewed GitHub stars and browser bookmarks. Entries are reading/evaluation candidates, not endorsements; nothing is installed, cloned or executed by Workbench. Repository descriptions are self-reported by their authors.

### Agent skills, harnesses and workflows

- Skill collections: [mattpocock/skills](https://github.com/mattpocock/skills), [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills), [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents), [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), [TechNomadCode/AI-Product-Development-Toolkit](https://github.com/TechNomadCode/AI-Product-Development-Toolkit).
- Curated lists: [awesome-claude-code](https://github.com/jqueryscript/awesome-claude-code), [awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit), [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice), [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers), [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps).
- Harnesses: [opencode](https://github.com/anomalyco/opencode), [hermes-agent](https://github.com/NousResearch/hermes-agent), [jcode](https://github.com/1jehuang/jcode), [deepseek-harness](https://github.com/deepseek-ai/deepseek-harness).
- Continuity and cost: [ai-memory](https://github.com/akitaonrails/ai-memory) (cross-CLI memory and handoff; compare with `aiwh resume`), [TokenEconomizer](https://github.com/microsoft/TokenEconomizer).
- Code understanding: [Understand-Anything](https://github.com/Egonex-AI/Understand-Anything), [craft-anything](https://github.com/storytold/craft-anything), [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x).
- Computer/browser use: [agent-desktop](https://github.com/vercel-labs/agent-desktop), [Lightpanda](https://github.com/lightpanda-io/browser).

### Code review and security (authorized use only)

- AI PR review: [opencodereview](https://github.com/BridgLabs/opencodereview), [alibaba/open-code-review](https://github.com/alibaba/open-code-review).
- Audits and pentest automation: [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill), [Shannon](https://github.com/KeygraphHQ/shannon), [guardian-cli](https://github.com/zakirkun/guardian-cli).
- Learning path: [The-BlackHAT-roadmap](https://github.com/SagarBiswas-MultiHAT/The-BlackHAT-roadmap).

### Reverse engineering with agents

- REA ecosystem: [rea](https://github.com/morluto/rea), [leanrea](https://github.com/aicodeking/leanrea) (CLI-only alternative without MCP), [REA-Prompts](https://github.com/JoasASantos/REA-Prompts), [rea-lab](https://github.com/pablodiazjorge/rea-lab), [Awesome-REA](https://github.com/reacher-z/Awesome-REA), [awesome-reverse-engineer-anything](https://github.com/AIshihzong/awesome-reverse-engineer-anything).
- Example rebuilds: [rec-rs](https://github.com/michaelshimeles/rec-rs), [dx-ball](https://github.com/N0zoM1z0/dx-ball).
- Game modding: [universal-modder](https://github.com/rehan-remade/universal-modder); matching decomp: [decomp.wtf](https://github.com/i12bp8/decomp.wtf) (see the integration note in [GAME_PORTING.md](GAME_PORTING.md)).
- MCP candidates and utilities are routed through `capabilities/mcp/catalog.json` and `capabilities/utilities/README.md`.

### LLM learning and local models

- Courses: [llm-course](https://github.com/mlabonne/llm-course), [ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners), [RAG_Techniques](https://github.com/NirDiamant/RAG_Techniques).
- Local inference: [pocketpal-ai](https://github.com/a-ghorbani/pocketpal-ai), [kimi-k3-in-c](https://github.com/FareedKhan-dev/kimi-k3-in-c), [kokoro](https://github.com/hexgrad/kokoro) (TTS), [VoiceStudio](https://github.com/debpalash/VoiceStudio).

### Content, media and marketing

- Video/media: [OpenCut](https://github.com/OpenCut-app/OpenCut), [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), [HeliosGen](https://github.com/SegFault42/HeliosGen), [rea-video](https://github.com/JuneYaooo/rea-video), [motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills), [anatomy](https://github.com/wheresryan22/anatomy).
- Research skills: [last30days-skill](https://github.com/mvanhorn/last30days-skill), [social-media-research-skills](https://github.com/ScrapeCreators/social-media-research-skills), [appllama-skills](https://github.com/Appllama/appllama-skills).

### Quantitative finance (`quant-finance` area)

Routed by the `quant-finance` area and `wb-quant-research` skill. Research/backtesting references only; none constitute financial advice and live trading needs separate risk review: [OpenBB](https://github.com/openbq-org/OpenBB), [freqtrade](https://github.com/freqtrade/freqtrade), [TradingAgents](https://github.com/TauricResearch/TradingAgents), [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading), [Kronos](https://github.com/shiyu-coder/Kronos), [daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis), [tick-stock-panel](https://github.com/shy3130/tick-stock-panel), [trader-skill](https://github.com/Jakeschincariol/trader-skill), [day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill), [awesome-quant](https://github.com/wilsonfreitas/awesome-quant).

### QA (Portuguese-language)

- [gen-ai-para-produtividade-em-testes](https://github.com/juliodelimas/gen-ai-para-produtividade-em-testes), [api-clientes-exemplo-microservico](https://github.com/vinnypessoni/api-clientes-exemplo-microservico).

### Security research and red-team references (authorized testing only)

Listed for defensive study, model-safety evaluation and authorized engagements. Do not run against systems, devices or accounts you do not own or have written permission to test.

- Offensive toolkits and scanners: [hackingtool](https://github.com/Z4nzu/hackingtool), [php2shell-scanner](https://github.com/assetnote/php2shell-scanner).
- Android privilege escalation research: [CVE-2026-43499-root-KernelSU](https://github.com/woshimaniubi8/CVE-2026-43499-root-KernelSU).
- LLM safety/jailbreak corpora (red-teaming evaluation): [togg53192-cmd/jailbreaks](https://github.com/togg53192-cmd/jailbreaks), [ai-jailbreaks](https://github.com/Alejandros17487/ai-jailbreaks), [antigravity-filter-bypass](https://github.com/v1ktorrr0x/antigravity-filter-bypass).

### LLM gateways and providers (check provider terms before use)

[free-claude-code](https://github.com/Alishahryar1/free-claude-code), [freellmapi](https://github.com/tashfeenahmed/freellmapi), [OmniRoute](https://github.com/cheaper-inference/OmniRoute), [ZenMux](https://zenmux.ai/platform/gift-center), [Vyce AI](https://vyceai.com/dashboard-v2), [locally-uncensored](https://github.com/PurpleDoubleD/locally-uncensored).

### Desktop, mobile and productivity tools

- Windows/PC: [g-helper](https://github.com/seerge/g-helper), [Magpie](https://github.com/Blinue/Magpie), [gpu-unlock](https://github.com/Zagitta/gpu-unlock), [MFG-SUPER-MOTION](https://github.com/NODIX-TECH/MFG-SUPER-MOTION), [hatchzip](https://github.com/xevrion/hatchzip), [photocraft](https://github.com/storytold/photocraft).
- Downloads/media: [omniget](https://github.com/OpenSelena/omniget), [yoinks](https://github.com/pablostanley/yoinks).
- Android/TV: [ImageToolbox](https://github.com/T8RIN/ImageToolbox), [blockads-android](https://github.com/pass-with-high-score/blockads-android), [cleanyourtv](https://github.com/Gathin23/cleanyourtv), [FreeMyTvWebOS](https://github.com/danielthejoker18/FreeMyTvWebOS).
- Messaging: [zapfast](https://github.com/crmne/zapfast), [WA-AKG](https://github.com/mrifqidaffaaditya/WA-AKG).
- Browser: [awesome-userscripts](https://github.com/awesome-scripts/awesome-userscripts).

### Gaming

- Launchers/catalogs (verify content licensing): [Hydra Launcher](https://github.com/hydralauncher/hydra), [PS3-Game-Scraper](https://github.com/NookieAI/PS3-Game-Scraper).
- Mods and community: [Ocarina of Time controller UI mod](https://gamebanana.com/mods/737074), [Mundo Guitar Hero](https://mundoguitarhero.blogspot.com).
- Additional ports/runtimes: [Supermedo/bloodborne_pc](https://github.com/Supermedo/bloodborne_pc), [cuesta4/shadPS4](https://github.com/cuesta4/shadPS4) (fork), plus the platform tables in [GAME_PORTING.md](GAME_PORTING.md).

### Guides and threads

- [Claude Code para Reverse Engineering](https://x.com/Gyome1_/status/2111774069783720195), [Reverse Engineering com Opus](https://x.com/0xMovez/status/2109604520770548146), [GitHub topic: android-reverse-engineering](https://github.com/topics/android-reverse-engineering).

### Other projects

[louvorja/desktop](https://github.com/louvorja/desktop), [gerenciador-viagens](https://github.com/AntonioMontanha/gerenciador-viagens) (Java study project, QA practice).
