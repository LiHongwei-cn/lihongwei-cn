# Automotive Safety Skills - ISO 26262 Functional Safety

Comprehensive ISO 26262:2018 functional safety skills for ASIL-D automotive E/E system development. All skills are production-ready with real-world examples, templates, and code.

## Skills Overview

### 1. ISO 26262 Overview
**File:** `iso-26262-overview.md`
**Topics:** Complete standard overview, V-model, ASIL determination, safety goals, metrics
**Use For:** New projects, training, phase gate preparation

### 2. Hazard Analysis and Risk Assessment (HARA)
**File:** `hazard-analysis-risk-assessment.md`
**Topics:** HARA methodology, S/E/C classification, ASIL determination, templates
**Use For:** Concept phase, safety goal definition, risk assessment

### 3. Safety Mechanisms and Patterns
**File:** `safety-mechanisms-patterns.md`
**Topics:** Redundancy, watchdogs, CRC, memory protection, plausibility checks
**Use For:** Safety architecture design, diagnostic coverage improvement

### 4. FMEA/FTA Analysis
**File:** `fmea-fta-analysis.md`
**Topics:** FMEA/FMEDA/FTA methodology, metrics calculation, tools
**Use For:** Safety analysis, metrics verification, design optimization

### 5. Software Safety Requirements
**File:** `software-safety-requirements.md`
**Topics:** ASIL-D software development, MISRA, MC/DC testing, safety manual
**Use For:** Software development, code reviews, unit testing

### 6. Safety Verification and Validation
**File:** `safety-verification-validation.md`
**Topics:** V&V methods, HIL testing, fault injection, traceability, assessment
**Use For:** Verification planning, HIL testing, safety assessment preparation

## Quick Reference

### By ASIL Level

**ASIL-A:**
- Basic HARA
- Simple FMEA
- Standard testing

**ASIL-B:**
- HARA with exposure data
- Detailed FMEA
- SPFM > 90%, PMHF < 100 FIT
- Branch coverage testing

**ASIL-C:**
- HARA + FTA
- FMEA + FTA
- SPFM > 97%, LFM > 80%, PMHF < 100 FIT
- MC/DC coverage (recommended)

**ASIL-D:**
- Complete HARA + FTA
- FMEDA with all metrics
- SPFM > 99%, LFM > 90%, PMHF < 10 FIT
- MC/DC coverage (mandatory)
- Independent assessment

### By Development Phase

**Concept Phase:**
- Use: `iso-26262-overview.md`, `hazard-analysis-risk-assessment.md`
- Deliverables: Item Definition, HARA, Safety Goals, FSC

**System Development:**
- Use: `iso-26262-overview.md`, `fmea-fta-analysis.md`, `safety-mechanisms-patterns.md`
- Deliverables: TSC, System FMEA/FTA, Architecture

**Hardware Development:**
- Use: `fmea-fta-analysis.md`, `safety-mechanisms-patterns.md`
- Deliverables: FMEDA, Hardware Metrics, Safety Mechanisms

**Software Development:**
- Use: `software-safety-requirements.md`, `safety-mechanisms-patterns.md`
- Deliverables: SWR, Code, Unit Tests, Safety Manual

**Verification & Validation:**
- Use: `safety-verification-validation.md`
- Deliverables: V&V Plan, Test Results, Traceability

## Code Examples Summary

### C/C++ (1500+ lines)
- Redundancy patterns (1oo2, 2oo3, lockstep)
- Watchdog mechanisms
- CRC/checksum implementations
- Memory protection (RAM test, stack monitoring)
- Plausibility checks
- Safe state management

### Python (800+ lines)
- FMEDA calculator
- FTA probability analysis
- HIL test framework
- Mutation testing
- Traceability tools

### SQL (500+ lines)
- HARA database
- FMEA database
- Traceability database
- Assessment tracking

## Templates Included

**Analysis Templates:**
- HARA worksheet (YAML, Excel, SQL)
- FMEA/FMEDA spreadsheet
- FTA diagrams
- DFA report

**Requirements Templates:**
- Software Safety Requirements (YAML)
- Traceability matrix
- Verification matrix

**Test Templates:**
- Unit test suites (Unity/C)
- HIL test scripts (Python)
- Fault injection scenarios

**Documentation Templates:**
- Software Safety Manual
- Assessment Report
- Safety Case

## Related Content

**Agents:**
- `/agents/functional-safety/safety-engineer.md` - Expert safety engineer
- `/agents/functional-safety/safety-assessor.md` - Independent assessor

**Summary:**
- `/FUNCTIONAL_SAFETY_DELIVERABLES.md` - Complete package overview

## Usage Examples

### Example 1: New ASIL-D ECU Project

```bash
# Phase 1: Learn ISO 26262 basics
Read: iso-26262-overview.md

# Phase 2: Perform HARA
Read: hazard-analysis-risk-assessment.md
Use: HARA templates (YAML/Excel)
Output: HARA report with safety goals

# Phase 3: Design safety architecture
Read: safety-mechanisms-patterns.md
Use: Redundancy patterns, watchdog code
Output: Technical safety concept

# Phase 4: Perform safety analysis
Read: fmea-fta-analysis.md
Use: FMEDA calculator, FTA tools
Output: FMEA/FTA reports, metrics

# Phase 5: Develop software
Read: software-safety-requirements.md
Use: MISRA guidelines, unit test templates
Output: ASIL-D compliant code

# Phase 6: Verify and validate
Read: safety-verification-validation.md
Use: HIL test scripts, fault injection
Output: Verification reports
```

### Example 2: Improve PMHF

```bash
# Current: PMHF = 16 FIT (target: < 10 FIT)

# Step 1: Analyze contributors
Read: fmea-fta-analysis.md (FMEDA section)
Tool: Python FMEDA calculator

# Step 2: Identify high contributors
# Find: Sensor FL = 15 FIT (94% of total)

# Step 3: Evaluate improvements
Read: safety-mechanisms-patterns.md (Redundancy section)
Options: 1oo2 redundancy OR improve DC

# Step 4: Implement and recalculate
Code: 1oo2 voter implementation
Result: PMHF = 1.65 FIT ✓
```

### Example 3: Prepare for Assessment

```bash
# Assessment in 4 weeks

# Week 1: Self-assessment
Read: safety-verification-validation.md (Assessment section)
Tool: Assessment checklist
Output: Gap analysis

# Week 2: Close critical gaps
Read: Relevant skills for each gap
Example: MC/DC coverage → software-safety-requirements.md

# Week 3: Prepare evidence
Tool: Traceability database
Output: Complete evidence package

# Week 4: Mock assessment
Agent: safety-assessor.md
Output: Readiness confirmation
```

## Best Practices

### Document Organization
- Use version control (Git) for all work products
- Maintain traceability (SG → FSR → TSR → SWR → Code → Test)
- Review all documents before phase gate
- Keep configuration management up-to-date

### Code Quality
- Follow MISRA C:2012 / MISRA C++:2008
- Achieve 100% MC/DC for ASIL-D
- Use static analysis (PC-Lint, Polyspace)
- Conduct code reviews

### Testing Strategy
- Unit tests: 100% MC/DC coverage
- Integration tests: All interfaces
- System tests: All requirements
- HIL tests: 1000+ hours for ASIL-D
- Fault injection: All safety mechanisms

### Safety Analysis
- FMEA at component level (not too high-level)
- FTA for all ASIL C/D safety goals
- DFA for ASIL decomposition
- Verify metrics meet targets

## Metrics Targets

| ASIL | SPFM | LFM | PMHF | Test Coverage |
|------|------|-----|------|---------------|
| A | - | - | < 1000 FIT | Statement |
| B | > 90% | > 60% | < 100 FIT | Branch |
| C | > 97% | > 80% | < 100 FIT | MC/DC (recommended) |
| D | > 99% | > 90% | < 10 FIT | MC/DC (mandatory) |

## Tool Recommendations

**Analysis:**
- Medini Analyze (Ansys)
- APIS IQ-Software

**Development:**
- MATLAB/Simulink (with IEC Cert Kit)
- SCADE Suite
- TargetLink

**Testing:**
- Vector CANoe/CANalyzer
- dSPACE HIL
- LDRA (unit test + coverage)

**Static Analysis:**
- Polyspace
- PC-Lint / Flexelint
- Klocwork

## Troubleshooting

### Common Issues

**PMHF exceeds target:**
- Check FMEDA contributors (use Python calculator)
- Improve diagnostic coverage (safety-mechanisms-patterns.md)
- Add redundancy (1oo2, 2oo3)

**MC/DC coverage < 100%:**
- Identify missing test cases (software-safety-requirements.md)
- Use coverage tool (LDRA, gcov)
- Add boundary value tests

**HARA completeness questioned:**
- Review all operational situations (hazard-analysis-risk-assessment.md)
- Justify S/E/C with evidence
- Cross-check with accident databases

**Traceability gaps:**
- Use traceability database (SQL templates)
- Automate link generation
- Verify bidirectional links

## References

- ISO 26262:2018 (all 12 parts)
- ISO/PAS 21448:2019 (SOTIF)
- ISO/SAE 21434:2021 (Cybersecurity)
- MISRA C:2012
- MISRA C++:2008
- AUTOSAR Safety specifications

## Version History

- v1.0 (2024-03-19): Initial release
  - 6 comprehensive skills
  - 2500+ lines of code
  - 25+ templates
  - Complete ASIL-D coverage

## License

Open for automotive safety community use.
Authentication-free, production-ready content.

---

**For detailed information, see:**
`/FUNCTIONAL_SAFETY_DELIVERABLES.md`
