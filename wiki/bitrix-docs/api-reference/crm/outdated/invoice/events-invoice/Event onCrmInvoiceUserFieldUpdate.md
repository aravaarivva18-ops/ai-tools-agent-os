---
tags:
  - bitrix
  - api
  - docs
title: "Event onCrmInvoiceUserFieldUpdate"
original_path: "api-reference/crm/outdated/invoice/events-invoice/on-crm-invoice-user-field-update.md"
---

# Event onCrmInvoiceUserFieldUpdate

{% note tip "" %}

If you are developing integrations for Bitrix24 using AI tools (Codex, Claude Code, Cursor), connect to the [MCP server](../../../../../ai-tools/mcp.md) so that the assistant can utilize the official REST documentation.

{% endnote %}

The event is triggered when a custom field is updated.

## Parameters

{% include [Note on required parameters](../../../../../_includes/required.md) %}

#|
|| **Name**
`type` | **Description** ||
|| **id** 
[`integer`](../../../../data-types.md)| Identifier of the custom field ||
|| **entityId** 
[`string`](../../../../data-types.md)| Symbolic identifier of the entity for which the field was created ||
|| **fieldName** 
[`string`](../../../../data-types.md)| Name of the created custom field ||
|#