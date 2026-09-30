Extract lab/report values exactly as printed in the text.

Rules:
- Copy value, unit and the printed reference range verbatim.
- Do NOT say whether a value is normal, abnormal, high, low, improving or worsening.
- Do NOT add flags, interpretations or conclusions.
- Include source_line: the exact line each value came from.

Return JSON:
{"report_type":"","report_date":"","values":[{"name":"","value":"","unit":"","reference_range_as_printed":"","source_line":""}]}
