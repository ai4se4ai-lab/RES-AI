# Bibliography audit (2026-10-30 UTC)

Reviewed all 70 bibliography records and 12 artifact citation records. Verification concerns bibliographic identity and publication metadata, not an endorsement of paper findings. Search hits were candidates only; unmatched results were never substituted.

Published venue versions replace preprints when a publisher/proceedings or official author record establishes the match. CORE-Bench is TMLR 2025; EnvBench is the ICLR 2025 Deep Learning for Code workshop; ExecutionAgent is PACMSE 2(ISSTA), 2025. MetaGPT and OpenHands use their published proceedings author lists. Missing authors, identifiers and pagination were corrected from publisher metadata. Stable keys can contain the former preprint year.

The Baltes guidelines are accepted at EMSE according to the authors; no final DOI/pages were verified, so the record explicitly retains an author-preprint link. OpenAlex, AgentCoder, HyperAgent and the version-2 empirical standards retain preprint records: no published replacement was established. An ICLR submission alone is not proof of publication. The HyperAgent repository contains a conflicting arXiv identifier, so arXiv metadata takes precedence.

**Remaining limits:** the ACM badging page and Alliance documentation site block automated access. Their existing official-resource records are retained and marked access-limited, not certified as freshly verified. No unmatched scholarly record was labeled verified, and no record was declared fabricated merely because a service blocked retrieval.

| Key | Disposition | Primary / deposited metadata source | Changed fields |
|---|---|---|---|
| `jimenez2024swebench` | VERIFIED_PRIMARY_SOURCE | [source](https://openreview.net/pdf?id=VTF8yNQM66) | url |
| `yang2024sweagent` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=SWE-agent%3A+Agent-Computer+Interfaces+Enable+Automated+Software+Engineering&rows=3) | author, booktitle, doi, pages, publisher, title, url |
| `liu2023evalplus` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Is+Your+Code+Generated+by+ChatGPT+Really+Correct%3F+Rigorous+Evaluation+of+Large+Language+Models+for+Code+Generation&rows=3) | author, booktitle, doi, pages, publisher, title, url |
| `du2024classeval` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/3597503.3639219) | author, booktitle, pages, publisher, title, url |
| `sallou2024breaking` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/3639476.3639764) | author, booktitle, publisher, title, url |
| `baltes2025guidelines` | VERIFIED_ACCEPTED_FINAL_METADATA_PENDING | [source](https://llm-guidelines.org/) | ENTRYTYPE, author, howpublished, journal, note, url, year |
| `yoo2003slurm` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1007%2F10968987_3) | ENTRYTYPE, address, author, booktitle, publisher, series, title, url |
| `pimentel2019jupyter` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1109/MSR.2019.00077) | author, booktitle, doi, publisher, title, url |
| `trisovic2022research` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1038/s41597-022-01143-6) | author, number, publisher, title, url |
| `collberg2016repeatability` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/2812803) | author, publisher, title, url |
| `timperley2021artifact` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1007%2Fs10664-021-09973-5) | author, publisher, title, url |
| `liu2024artifacts` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Research+Artifacts+in+Software+Engineering+Publications%3A+Status+and+Trends&rows=3) | ENTRYTYPE, author, doi, howpublished, journal, pages, publisher, title, url, volume |
| `anthropic2025skills` | VERIFIED_OFFICIAL_WEB_RESOURCE | [source](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) | author, note |
| `priem2022openalex` | VERIFIED_PREPRINT_NO_PUBLISHED_VERSION_CONFIRMED | [source](https://arxiv.org/abs/2205.01833) | author, url |
| `deelman2015pegasus` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1016/j.future.2014.10.008) | author, publisher, title, url |
| `molder2021snakemake` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.12688/f1000research.29032.1) | author, publisher, title, url |
| `ditommaso2017nextflow` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1038/nbt.3820) | author, publisher, title, url |
| `babuji2019parsl` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/3307681.3325400) | author, booktitle, publisher, title, url |
| `chirigati2016reprozip` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/2882903.2899401) | author, booktitle, publisher, title, url |
| `dyer2013boa` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1109/ICSE.2013.6606588) | author, booktitle, doi, publisher, title, url |
| `bogin2024super` | VERIFIED_PRIMARY_SOURCE | [source](https://aclanthology.org/2024.emnlp-main.702/) | address, author, booktitle, doi, editor, month, publisher, url |
| `siegel2024corebench` | VERIFIED_PRIMARY_SOURCE | [source](https://openreview.net/pdf?id=BsMMc4MEGS) | journal, title, url, year |
| `starace2025paperbench` | VERIFIED_PRIMARY_SOURCE | [source](https://proceedings.mlr.press/v267/starace25a.html) | author, booktitle, publisher, series, url |
| `nichols2024hpccoder` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.23919%2FISC.2024.10528929) | author, booktitle, doi, pages, publisher, title, url |
| `jimenez2017popper` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1109/IPDPSW.2017.157) | author, booktitle, doi, publisher, title, url |
| `wang2025semguard` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.title=Semguard%3A+Real-time+semantic+evaluator+for+correcting+llm-generated+code&rows=3) | doi, organization, publisher, title, url |
| `she2026provenanceguard` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Safeguarding+LLM+Agents+from+Misalignment+through+Provenance+Analysis&rows=3) | doi, publisher, title, url |
| `zhang2025retrigen` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/3721128) | author, journal, note, number, pages, publisher, title, url, volume |
| `dong2026execre` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=ExeCRE%3A+Execution-Consistency+Guided+Reliability+Estimation+for+Self-Correcting+Code+Generation&rows=3) | doi, publisher, title, url |
| `yu2026effiskel` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Chiseling+Out+Efficiency%3A+Structured+Skeleton+Supervision+for+Efficient+Code+Generation&rows=3) | author, doi, publisher, title, url |
| `li2026binaryspd` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145%2F3822506) | author, journal, note, publisher, title, url |
| `li2024ircoco` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1145/3643735) | doi, publisher, title, url |
| `rabbi2026robustness` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.title=A+multi-language+perspective+on+the+robustness+of+LLM+code+generation&rows=3) | doi, publisher, title, url |
| `wang2026llm4perf` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=LLM4Perf%3A+Large+Language+Models+Are+Effective+Samplers+for+Multi-Objective+Performance+Modeling&rows=3) | doi, publisher, title, url |
| `ma2026logreasoner` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1145/3801747) | author, journal, note, publisher, title, url |
| `jain2015fireworks` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=FireWorks%3A+a+dynamic+workflow+system+designed+for+high-throughput+applications&rows=3) | author, doi, publisher, title, url |
| `gundersen2018state` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=State+of+the+art%3A+Reproducibility+in+artificial+intelligence&rows=3) | ENTRYTYPE, booktitle, doi, journal, number, publisher, title, url |
| `pineau2021improving` | VERIFIED_PRIMARY_SOURCE | [source](https://www.jmlr.org/papers/v22/20-303.html) | url |
| `stodden2016enhancing` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1126/science.aah6168) | author, doi, publisher, title, url |
| `baker2016reproducibility` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=1%2C500+scientists+lift+the+lid+on+reproducibility&rows=3) | doi, number, publisher, title, url |
| `wilkinson2016fair` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1038/sdata.2016.18) | author, doi, number, publisher, title, url |
| `acm2020badges` | ACCESS_LIMITED_OFFICIAL_RESOURCE | [source](https://www.acm.org/publications/policies/artifact-review-and-badging-current) |  |
| `kurtzer2017singularity` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Singularity%3A+Scientific+containers+for+mobility+of+compute&rows=3) | doi, journal, publisher, title, url |
| `vitek2011repeatability` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1145/2038642.2038650) | address, booktitle, doi, title, url |
| `hoefler2015scientific` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145%2F2807591.2807644) | address, booktitle, pages, title, url |
| `wang2025openhands` | VERIFIED_PRIMARY_SOURCE | [source](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a4b6ad6b48850c0c331d1259fc66a69c-Abstract-Conference.html) | author, booktitle, url |
| `kwon2023vllm` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.title=Efficient+Memory+Management+for+Large+Language+Model+Serving+with+%7BPagedAttention%7D&rows=3) | address, author, booktitle, doi, title, url |
| `wohlin2012experimentation` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1007/978-3-642-29044-2) | address, doi, publisher, url |
| `meyer1992dbc` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Applying+%60%60Design+by+Contract%27%27&rows=3) | author, doi, publisher, title, url |
| `nvidia2023mig` | VERIFIED_OFFICIAL_WEB_RESOURCE | [source](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/) | note, year |
| `alliance2026docs` | ACCESS_LIMITED_OFFICIAL_RESOURCE | [source](https://docs.alliancecan.ca) |  |
| `usehpc2026repo` | VERIFIED_OFFICIAL_WEB_RESOURCE | [source](https://github.com/ai4se4ai-lab/use-hpc-claude-skill) | note |
| `baek2026artisan` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Automated+Table+Reproduction+via+Code+Generation&rows=3) | doi, publisher, title, url |
| `bouzenia2025executionagent` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=You+Name+It%2C+I+Run+It%3A+An+LLM+Agent+to+Execute+Tests+of+Arbitrary+Projects&rows=3) | ENTRYTYPE, author, booktitle, doi, journal, note, number, pages, publisher, title, url, volume |
| `wang2026agentspec` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145/3744916.3764546) | author, booktitle, publisher, title, url |
| `eliseeva2025envbench` | VERIFIED_PRIMARY_SOURCE | [source](https://github.com/JetBrains-Research/EnvBench) | ENTRYTYPE, booktitle, journal, title, url |
| `hu2025repo2run` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Repo2Run%3A+Automated+Building+Executable+Environment+for+Code+Repository+at+Scale&rows=3) | author, booktitle, doi, note, pages, publisher, title, url, volume |
| `huang2024mlagentbench` | VERIFIED_PRIMARY_SOURCE | [source](https://proceedings.mlr.press/v235/huang24y.html) | booktitle, pages, publisher, series, url |
| `crusoe2022cwl` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1145%2F3486897) | author, publisher, title, url |
| `adorf2018signac` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1016/j.commatsci.2018.01.035) | author, publisher, title, url |
| `greff2017sacred` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.25080/shinma-7f4c6e7-008) | author, booktitle, publisher, title, url |
| `davison2012sumatra` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1109/MCSE.2012.41) | author, doi, publisher, title, url |
| `silva2021topic` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Topic+modeling+in+software+engineering+research&rows=3) | doi, publisher, title, url |
| `yang2022predictive` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=Predictive+models+in+software+engineering%3A+Challenges+and+opportunities&rows=3) | doi, journal, publisher, title, url |
| `kapitsaki2026does` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.title=Where+does+Software+Engineering+research+funding+come+from%3F+A+bibliometric+study+in+top+venues+%281975-2023%29&rows=3) | author, doi, publisher, title, url |
| `usehpc2026eval` | VERIFIED_OFFICIAL_WEB_RESOURCE | [source](https://github.com/ai4se4ai-lab/use-hpc-evaluation) | note |
| `schedmdScheduling` | VERIFIED_OFFICIAL_WEB_RESOURCE | [source](https://slurm.schedmd.com/sched_config.html) | note |
| `mcp2024transport` | VERIFIED_OFFICIAL_WEB_RESOURCE | [source](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports) | note |
| `ralph2021standards` | VERIFIED_PREPRINT_NO_PUBLISHED_VERSION_CONFIRMED | [source](https://arxiv.org/abs/2010.03525v2) | author, howpublished, url |
| `runeson2009guidelines` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works/10.1007/s10664-008-9102-8) | author, number, publisher, title, url |
| `resaiartifact1` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=SWE-agent%3A+Agent-Computer+Interfaces+Enable+Automated+Software+Engineering&rows=3) | ENTRYTYPE, author, booktitle, doi, howpublished, pages, publisher, url, volume |
| `resaiartifact2` | VERIFIED_PRIMARY_SOURCE | [source](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a4b6ad6b48850c0c331d1259fc66a69c-Abstract-Conference.html) | ENTRYTYPE, author, booktitle, howpublished, title, url, year |
| `resaiartifact3` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.title=%7BAutoCodeRover%3A+Autonomous+Program+Improvement%7D&rows=3) | ENTRYTYPE, booktitle, doi, howpublished, pages, publisher, url |
| `resaiartifact4` | VERIFIED_PRIMARY_SOURCE | [source](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html) | ENTRYTYPE, author, booktitle, howpublished, url, year |
| `resaiartifact5` | VERIFIED_PRIMARY_SOURCE | [source](https://aclanthology.org/2024.acl-long.810/) | ENTRYTYPE, address, author, booktitle, doi, editor, howpublished, month, pages, publisher, title, url, year |
| `resaiartifact6` | VERIFIED_PREPRINT_NO_PUBLISHED_VERSION_CONFIRMED | [source](https://arxiv.org/abs/2312.13010) | howpublished, url |
| `resaiartifact7` | VERIFIED_PRIMARY_SOURCE | [source](https://aclanthology.org/2024.acl-long.269/) | ENTRYTYPE, address, author, booktitle, doi, editor, howpublished, month, pages, publisher, title, url |
| `resaiartifact8` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1109/ICSE55347.2025.00157) | ENTRYTYPE, booktitle, doi, howpublished, pages, publisher, url, year |
| `resaiartifact9` | VERIFIED_PUBLISHER_METADATA | [source](https://api.crossref.org/works?query.bibliographic=You+Name+It%2C+I+Run+It%3A+An+LLM+Agent+to+Execute+Tests+of+Arbitrary+Projects&rows=3) | ENTRYTYPE, doi, howpublished, journal, number, pages, publisher, url, volume, year |
| `resaiartifact10` | VERIFIED_PRIMARY_SOURCE | [source](https://proceedings.mlr.press/v235/wang24h.html) | ENTRYTYPE, author, booktitle, howpublished, pages, publisher, series, url, volume |
| `resaiartifact11` | VERIFIED_PREPRINT_NO_PUBLISHED_VERSION_CONFIRMED | [source](https://arxiv.org/abs/2409.16299) | howpublished, url |
| `resaiartifact12` | VERIFIED_PUBLISHER_METADATA | [source](https://doi.org/10.1109/FORGE66646.2025.00026) | ENTRYTYPE, author, booktitle, doi, howpublished, pages, publisher, url, year |
