---
tags:
  - bitrix
  - api
  - docs
title: "Task Template Fields"
original_path: "api-reference/tasks/template/fields.md"
---

# Task Template Fields

{% note tip "" %}

If you are developing integrations for Bitrix24 using AI tools (Codex, Claude Code, Cursor), connect to the [MCP server](../../../ai-tools/mcp.md) so that the assistant can utilize the official REST documentation.

{% endnote %}

#|
|| **Name**
`type` | **Description** ||
|| **ID**
[`integer`](../../data-types.md) | Template identifier. In `tasks.template.add`, the input field `ID` is ignored and removed before saving ||
|| **PARENT_ID**
[`integer`](../../data-types.md) | Parent task identifier. Default is `0` ||
|| **TITLE**
[`string`](../../data-types.md) | Template title ||
|| **DESCRIPTION**
[`string`](../../data-types.md) | Template description ||
|| **PRIORITY**
[`enum`](../../data-types.md) | Priority ||
|| **GROUP_ID**
[`integer`](../../data-types.md) | Project identifier. Default is `0` ||
|| **STAGE_ID**
[`integer`](../../data-types.md) | Stage identifier. Default is `0` ||
|| **CREATED_BY**
[`integer`](../../data-types.md) | Creator identifier ||
|| **RESPONSIBLE_ID**
[`integer`](../../data-types.md) | Responsible person identifier ||
|| **DEPENDS_ON**
[`array`](../../data-types.md) | Array of template identifiers that the current template depends on. In the response `tasks.template.fields`, this field is described as `integer`, but in examples and when passed to `tasks.template.add` and `tasks.template.update`, an array is used ||
|| **RESPONSIBLES**
[`array`](../../data-types.md) | List of responsible persons ||
|| **ACCOMPLICES**
[`array`](../../data-types.md) | List of participants ||
|| **AUDITORS**
[`array`](../../data-types.md) | List of auditors ||
|| **STATUS**
[`enum`](../../data-types.md) | Status ||
|| **MULTITASK**
[`enum`](../../data-types.md) | Multitasking indicator. Possible values:
- `Y` — yes
- `N` — no

Default is `N` ||
|| **REPLICATE**
[`enum`](../../data-types.md) | Recurring task indicator. Possible values:
- `Y` — yes
- `N` — no

Default is `N` ||
|| **SITE_ID**
[`string`](../../data-types.md) | Site identifier ||
|| **TASK_CONTROL**
[`enum`](../../data-types.md) | Accept work. Possible values:
- `Y` — yes
- `N` — no

Default is `N` ||
|| **ADD_IN_REPORT**
[`enum`](../../data-types.md) | Add to report. Possible values:
- `Y` — yes
- `N` — no

Default is `N` ||
|| **XML_ID**
[`string`](../../data-types.md) | External identifier.

Default is `null` ||
|| **DEADLINE_AFTER**
[`datetime`](../../data-types.md) | Deadline after.

Default is `null` ||
|| **START_DATE_PLAN_AFTER**
[`datetime`](../../data-types.md) | Planned start after.

Default is `null` ||
|| **END_DATE_PLAN_AFTER**
[`datetime`](../../data-types.md) | Planned completion after.

Default is `null` ||
|| **TPARAM_TYPE**
[`enum`](../../data-types.md) | For new users. Default is `0` ||
|| **TPARAM_REPLICATION_COUNT**
[`integer`](../../data-types.md) | Number of created tasks. Default is `0` ||
|| **REPLICATE_PARAMS**
[`object`](../../data-types.md) | Template replication parameters [(detailed description)](#replicate_params) ||
|| **BASE_TEMPLATE_ID**
[`integer`](../../data-types.md) | Parent template identifier.

Default is `null` ||
|| **TEMPLATE_CHILDREN_COUNT**
[`integer`](../../data-types.md) | Number of child templates.

Default is `null` ||
|| **UF_* fields**
[`object`](../../data-types.md) | Custom fields of the object ||
|#

{% note info "" %}

To obtain a complete list of custom fields for a specific account, use `tasks.template.fields`.

{% endnote %}

## REPLICATE_PARAMS Parameter {#replicate_params}

### General Replication Parameters

#|
|| **Name**
`type` | **Description** ||
|| **PERIOD**
[`string`](../../data-types.md) | Type of repetition.

Possible values: `daily`, `weekly`, `monthly`, `yearly` ||
|| **START_DATE**
[`datetime`](../../data-types.md) | Start date and time of repetition in the format `31.12.2026 14:00:00`
||
|| **TIME**
[`string`](../../data-types.md) | Start time in the format `HH:MI`.

Default is `05:00` ||
|| **REPEAT_TILL**
[`string`](../../data-types.md) | Repetition end mode.

Possible values:
- `endless` — repetition without date and count limits
- `times` — repetition limited by the number of runs in `TIMES`
- `date` — repetition until the date specified in `END_DATE` ||
|| **TIMES**
[`integer`](../../data-types.md) | Number of repetitions.

Used when `REPEAT_TILL = times` ||
|| **END_DATE**
[`datetime`](../../data-types.md) | End date of repetition in the format `31.12.2026 14:00:00`.

Used when `REPEAT_TILL = date`
||
|| **NEXT_EXECUTION_TIME**
[`datetime`](../../data-types.md) | Date and time of the next execution ||
|| **DEADLINE_OFFSET**
[`integer`](../../data-types.md) | Deadline offset relative to the start time ||
|#

### Parameters for Daily Repetition `PERIOD = daily`

#|
|| **Name**
`type` | **Description** ||
|| **EVERY_DAY**
[`integer`](../../data-types.md) | Repetition interval in days.

Value from `1` ||
|| **WORKDAY_ONLY**
[`string`](../../data-types.md) | Consider only working days.

Possible values: `Y`, `N` ||
|| **DAILY_MONTH_INTERVAL**
[`integer`](../../data-types.md) | Additional interval for daily repetition.

Value from `0` ||
|#

### Parameters for Weekly Repetition `PERIOD = weekly`

#|
|| **Name**
`type` | **Description** ||
|| **EVERY_WEEK**
[`integer`](../../data-types.md) | Repetition interval in weeks.

Value from `1` ||
|| **WEEK_DAYS**
[`array`](../../data-types.md) | Days of the week for execution.

Possible values for array elements: `1..7`.

`1` — Monday, `2` — Tuesday, `3` — Wednesday, `4` — Thursday, `5` — Friday, `6` — Saturday, `7` — Sunday ||
|#

### Parameters for Monthly Repetition `PERIOD = monthly`

#|
|| **Name**
`type` | **Description** ||
|| **MONTHLY_TYPE**
[`integer`](../../data-types.md) | Type of monthly repetition.

Possible values: 
- `1` — by day of the month
- `2` — by day of the week ||
|| **MONTHLY_DAY_NUM**
[`integer`](../../data-types.md) | Day of the month.

Used when `MONTHLY_TYPE = 1`, value from `1` ||
|| **MONTHLY_MONTH_NUM_1**
[`integer`](../../data-types.md) | Month interval for the "by day of the month" scheme.

Used when `MONTHLY_TYPE = 1`, value from `1` ||
|| **MONTHLY_WEEK_DAY_NUM**
[`integer`](../../data-types.md) | Week number in the month.

Used when `MONTHLY_TYPE = 2`, possible values: `0..4`.

`0` — first week, `1` — second, `2` — third, `3` — fourth, `4` — last ||
|| **MONTHLY_WEEK_DAY**
[`integer`](../../data-types.md) | Day of the week in the "by day of the week" scheme.

Used when `MONTHLY_TYPE = 2`, possible values: `0..6`.

`0` — Monday, `1` — Tuesday, `2` — Wednesday, `3` — Thursday, `4` — Friday, `5` — Saturday, `6` — Sunday ||
|| **MONTHLY_MONTH_NUM_2**
[`integer`](../../data-types.md) | Month interval for the "by day of the week" scheme.

Used when `MONTHLY_TYPE = 2`, value from `1` ||
|#

### Parameters for Yearly Repetition `PERIOD = yearly`

#|
|| **Name**
`type` | **Description** ||
|| **YEARLY_TYPE**
[`integer`](../../data-types.md) | Type of yearly repetition.

Possible values:
- `1` — by day of the month
- `2` — by day of the week ||
|| **YEARLY_DAY_NUM**
[`integer`](../../data-types.md) | Day of the month.

Used when `YEARLY_TYPE = 1`, value from `1` ||
|| **YEARLY_MONTH_1**
[`integer`](../../data-types.md) | Month for the "by day of the month" scheme.

Used when `YEARLY_TYPE = 1`, possible values: `0..11`.

`0` — January, `1` — February, `2` — March, `3` — April, `4` — May, `5` — June, `6` — July, `7` — August, `8` — September, `9` — October, `10` — November, `11` — December ||
|| **YEARLY_WEEK_DAY_NUM**
[`integer`](../../data-types.md) | Week number in the month.

Used when `YEARLY_TYPE = 2`, possible values: `0..4`.

`0` — first week, `1` — second, `2` — third, `3` — fourth, `4` — last ||
|| **YEARLY_WEEK_DAY**
[`integer`](../../data-types.md) | Day of the week in the "by day of the week" scheme.

Used when `YEARLY_TYPE = 2`, possible values: `0..6`.

`0` — Monday, `1` — Tuesday, `2` — Wednesday, `3` — Thursday, `4` — Friday, `5` — Saturday, `6` — Sunday ||
|| **YEARLY_MONTH_2**
[`integer`](../../data-types.md) | Month for the "by day of the week" scheme.

Used when `YEARLY_TYPE = 2`, possible values: `0..11`.

`0` — January, `1` — February, `2` — March, `3` — April, `4` — May, `5` — June, `6` — July, `7` — August, `8` — September, `9` — October, `10` — November, `11` — December ||
|#