# YBC CFO OS — Start Here

**Yonkers Brewing Company LLC — Financial Operating System**
Owner: John Rubbo · Shared with: AJ · Version: August 2026

This folder is the portable brain of the YBC CFO agent. Upload every file in it
to a Claude Project (or attach them to a conversation) and Claude becomes the
brewery's CFO analyst — same rulebook, same numbers, same playbooks John uses.

## What's in the box

| File | What it is |
|------|-----------|
| `00_START_HERE.md` | This file — the map |
| `01_Business_Context.md` | The shape of the business: YTD numbers, the two-business thesis, who owns what |
| `02_Toast_QuickBooks_Category_Map.md` | The taxonomy: every Toast item → GL account, channel, revenue center; COGS targets; accounts to retire |
| `03_Exit_Readiness_Checklist.md` | The 10 diligence findings + 5 structural moves, with live statuses |
| `04_Per_Guest_Spend_Plan.md` | The per-guest decline, day-of-week economics, and the 10-move revenue plan |
| `05_CFO_Playbooks.md` | The four operating procedures: classification, weekly prime cost, exit readiness, per-guest tracking |
| `AJ_Claude_Upload_Prompt.md` | The prompt to paste into Claude after uploading — sets the rules of engagement |

## Ground rules (apply to every file)

1. **Numbers here are the baseline, not live data.** They come from live
   QuickBooks (July 26, 2026) and Toast (through July 22, 2026). When a
   QuickBooks or Toast connection is available, pull fresh; when it isn't,
   answer from these baselines and say the as-of date.
2. **Statuses change only on John's confirmation.** These documents record
   decisions; they don't make them.
3. **This is a planning and analysis aid, not a licensed accountant.** Tax
   filings and anything sale-ready goes through the CPA.
4. **Keep it inside the leadership circle** — John, AJ, Ian, Maria, Paul.
   These files contain real financials, member equity detail, and named
   employee performance data.

## Where the build lives

The source of truth is John's `chief` GitHub repo, `cfo/` directory — machine-
readable JSON versions of these documents plus Claude Code skills that run
against live QuickBooks. These markdown files are the shareable export of that
build. If a number here disagrees with the repo JSON, the repo wins.
