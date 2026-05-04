#!/usr/bin/env python
# encoding: utf-8
"""
Script to generate the default cliff config file.

All input values are passed as env-vars.
"""

import typing as _t
from typing import Any as _A, Optional as _O, Union as _U

from itertools import chain
from dataclasses import dataclass, asdict
import os
import re


__re_control_char = re.compile(r'[\x00-\x1f\x7f]')
# \x00–\x1f (0–31):
# The first 32 codepoints are all control characters -
# non-printable characters defined in the original ASCII standard.
# They include things like NUL (0), BEL (7), tab (9), newline (10),
# carriage return (13), ESC (27), etc.
# The range ends at 31 because codepoint 32 is a space,
# the first printable character.
#
# \x7f  (127):
# After the 95 printable ASCII characters (32–126), codepoint 127 is DEL:
# another control character, a historical artifact from the days
# of punched tape where you'd "delete" a character by punching
# ll 7 holes (binary 1111111 = 127).
# It's the one control character that's not in the 0–31 range,
# sitting just above the printable block instead.


def __re_control_char_replacer_for_toml(match: re.Match) -> str:
	"""Converts single control-character-match to TOML format."""
	codepoint = ord(match.group())
	return f'\\u{codepoint:04x}'


def toml_repr(string: str, dont_wrap_in_quotes = False) -> str:
	"""
	Do ``repr()``, but for TOML:
	Return the string representation as a TOML double-quoted string literal.
	"""
	for old, new in [
		('\\', '\\\\'),  # must be first
		('"', '\\"'),  # escape double-quotes
		# named control characters:
		('\n', '\\n'),
		('\r', '\\r'),
		('\t', '\\t'),
	]:
		string = string.replace(old, new)
	# For all the remaining control characters (\x00),
	# do a regex replacement (to \uXXXX):
	string = __re_control_char.sub(__re_control_char_replacer_for_toml, string)
	return string if dont_wrap_in_quotes else f'"{string}"'


def cleanup_as_single_line(string: str | None) -> str:
	"""Ensure the given string is a single line one."""
	if not string:
		return ''
	parts = (x.strip() for x in str(string).strip().splitlines())
	parts = (x for x in parts if x)
	try:
		return next(parts)
	except StopIteration:
		return ''


def is_true_str(str_bool: _O[str]) -> bool:
	"""Convert GitHub-action's "boolean" string into an actual bool."""
	str_bool = '' if str_bool is None else str(str_bool)
	str_bool = str_bool.strip()
	if not str_bool or str_bool.lower() == 'false':
		return False
	return True


@dataclass
class ConfigGenerator:
	cat_alert_blocks: bool = True

	cat_breaking: str = '💥 Breaking Changes 💥'
	cat_depr: str = '⚠️ Deprecations'
	cat_revert: str = '↩️ Rollbacks'
	cat_feat: str = '✨ New Features'
	cat_enhance: str = '🚀 Improvements'
	cat_fix: str = '🛠️ Fixes'
	cat_perf: str = '⚡ Performance'
	cat_security: str = '🔒 Security'
	cat_doc: str = '📝 Documentation'
	cat_refactor: str = '♻️ Refactor'
	cat_test: str = '🔬 Tests'
	cat_style: str = '🎨 Code Style'
	cat_build: str = '📦 Build/Packaging'
	cat_ci: str = '🤖 CI/CD'
	cat_chore: str = '🧹 Maintenance'
	cat_version: str = '🏷️ Version'
	cat_unclassified_multi: str = '🔀 Other changes'
	cat_unclassified_only: str = "⚙️ What's changed"

	github_owner: str = 'YOU MUST SPECIFY YOUR GitHub USERNAME'
	github_repo: str = 'YOU MUST SPECIFY YOUR GitHub REPO NAME'

	@staticmethod
	def __format_single_group_parsers(
		order:str = '0-0', group:str = 'Uncategorized',
		general_re: _t.Sequence[str] = tuple(),
		pr_re: _t.Sequence[str] = tuple(),
		msg_re: _t.Sequence[str] = tuple(),
		custom_pre_format: _t.Sequence[str] = tuple(),
		custom_post_format: _t.Sequence[str] = tuple(),
		pr_format: str = '{{ field = "remote.pr_title", pattern = {re}, group = {gr} }},',
		commit_format: str = '{{ message = {re}, group = {gr} }},',
		re_prefix: str  = re.compile(r'(?i)^[^a-zA-Z0-9]*?').pattern,
		custom_header_comment: str = '',
		add_leading_empty_line: bool = True,
	) -> _t.Iterable[str]:
		"""
		Generate ``commit_parsers`` lines for a single group.

		If ``custom_pre_format`` / ``custom_post_format`` used, they may contain:
			- ``{gr}`` - inserted group name.
			- ``{re_prefix}`` - the shared regex-prefix. If used, must be inside double-quoted string.

		:param order: String used for groups sorting in the output.
		:param group: Name (changelog title) of the group.
		:param general_re: regex patterns for both PRs and regular commits.
		:param pr_re: regex patterns only for PRs.
		:param msg_re: regex patterns only for non-PR commit messages.
		:param custom_pre_format: Custom lines format-string, added BEFORE other parsers.
		:param custom_post_format: Custom lines format-string, added AFTER other parsers.
		:return:
		"""
		order = cleanup_as_single_line(order)
		group = cleanup_as_single_line(group)
		gr_repr = toml_repr(f'<!-- {order} -->{group}')
		re_prefix_toml = toml_repr(re_prefix, dont_wrap_in_quotes=True)

		pre_lines: list[str] = list()
		pr_lines: list[str] = list()
		commit_lines: list[str] = list()
		post_lines: list[str] = list()

		for fmt in custom_pre_format:
			_lines = fmt.format(
				gr=gr_repr, re_prefix=re_prefix_toml
			).splitlines()
			pre_lines.extend(_lines)

		for re_pattern in general_re:
			re_repr = toml_repr(f'{re_prefix}{re_pattern}')
			_lines = pr_format.format(gr=gr_repr, re=re_repr).splitlines()
			pr_lines.extend(_lines)
			_lines = commit_format.format(gr=gr_repr, re=re_repr).splitlines()
			commit_lines.extend(_lines)

		for re_pattern in pr_re:
			re_repr = toml_repr(f'{re_prefix}{re_pattern}')
			_lines = pr_format.format(gr=gr_repr, re=re_repr).splitlines()
			pr_lines.extend(_lines)

		for re_pattern in msg_re:
			re_repr = toml_repr(f'{re_prefix}{re_pattern}')
			_lines = commit_format.format(gr=gr_repr, re=re_repr).splitlines()
			commit_lines.extend(_lines)

		for fmt in custom_post_format:
			parser_lines = fmt.format(
				gr=gr_repr, re_prefix=re_prefix_toml
			).splitlines()
			post_lines.extend(parser_lines)

		comment_text = '\n' + (
			custom_header_comment if custom_header_comment else group
		).strip()
		header = [f'# {ln}' for ln in comment_text.splitlines()]
		header[0] = ''  # Revert the first line back to empty one
		if not add_leading_empty_line:
			header = header[1:]

		return chain(
			header, pre_lines, pr_lines, commit_lines, post_lines
		)

	def __format_git_commit_parsers(self) -> _t.Iterable[str]:
		# `re.compile` used here only for syntax highlighting in IDE.
		# The actual regex syntax is for Rust.
		parser_lines = chain(
			"""
# Each category: PR-title field match first, then commit message match.
# Field matches only fire when remote.pr_title is set (i.e., actual PR merges),
# so they never interfere with regular commits.

# The "<!-- X-Y -->" prefix in each group name sets their display order.
# It's used only internally and never gets to the final output -
# thanks to "striptags" in the template.

# https://gitmoji.dev/

# Order-1
# ❗ Important warnings
			""".strip().splitlines(),

			self.__format_single_group_parsers(
				'1-1', self.cat_breaking,
				custom_pre_format=["""
# 1. Conventional breaking commits (feat!, fix!, BREAKING CHANGE footer) — native `cliff` field:
{{ breaking = true, group = {gr} }},
# 2. PR titles starting with "breaking" or the same "prefix!" pattern:
				""".strip()],
				general_re=[re.compile(
					r'('
					r'💥|❗|❕|‼️|‼|:boom:'
					r'|[a-zA-Z_]+(\([a-zA-Z_0-9-]+\))?!\s*:'
					r'|break(s|ing)?\b'
					r')'
				).pattern],
				custom_post_format=["""
# 3. Plain ^ commit messages with the same start
				""".strip()],
			),
			self.__format_single_group_parsers(
				'1-2', self.cat_depr, [re.compile(
					# r'🗑️'
					r'depr(ecat(ed?|ing|ion)?)?s?\b'
				).pattern],
			),
			self.__format_single_group_parsers(
				'1-3', self.cat_revert, [re.compile(
					r'('
					r'↩️|↩|↶|🔙|⏪️|⏪|:rewind:'
					r'|(revert|undo|(rl|roll)\s*(bk|back)s?)\b'
					r')'
				).pattern],
			),

			"""
# Order-2
# 👨🏻 User-oriented updates
			""".rstrip().splitlines(),

			self.__format_single_group_parsers(
				'2-1', self.cat_feat, [re.compile(
					r'('
					r'✨|🌟|⭐|🎉|:sparkles:|:tada:'
					r'|new(\([a-zA-Z_0-9-]+\))?!?\s*:'  # only explicit `new:`
					r'|(feat(ure)?|(add|support)(e?[ds]?|ing)?)\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'2-2', self.cat_enhance, [re.compile(
					r'('
					r'🚀|🚩|🚸|♿️'
					r'|:rocket:|:triangular_flag_on_post:'
					r'|:children_crossing:|:wheelchair:'
					r'|('
					r'upd(ate[ds]?)?'
					r'|chang(e[ds]?|ing)'
					r'|(enhn?c?|enhance?|impr|improve?)(e?[ds]?|ing|me?n?t?)?'
					r'|(more\s+)?(better|robust(ness)?)'
					r')\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'2-3', self.cat_fix, [re.compile(
					r'('
					r'🛠️|🛠|🐛|🩹|🚑️|🚑|🚨|🥅'
					r'|:bug:|:adhesive_bandage:|:ambulance:'
					r'|:rotating_light:|:goal_net:'
					r'|(bug(fix)?|fix(e?[ds]?|ing)?)\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'2-4', self.cat_perf, [re.compile(
					r'('
					r'⚡️|⚡|:zap:'
					r'|pe?rf(ormance)?\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'2-5', self.cat_security, [re.compile(
					r'('
					r'🔒|🔐|🛡️|🛡|:lock:|:closed_lock_with_key:'
					r'|sec(urity)?\b'
					r')'
				).pattern],
			),

			"""
# Order-3
# 👨🏻‍💻 Dev-oriented updates
			""".rstrip().splitlines(),

			self.__format_single_group_parsers(
				'3-1', self.cat_doc, [re.compile(
					r'('
					r'📝|📄|💬|:memo:|:page_facing_up:|:speech_balloon:'
					r'|(doc(ument)?(e?[ds]?|ing|ation)?|readme)\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'3-2', self.cat_refactor, [re.compile(
					r'('
					r'♻️|♻|🚚|:recycle:|:truck:'
					r'|('
					r'((full?|part(ial)?)(ly)?[^a-zA-Z0-9]*)?'
					r're[^a-zA-Z0-9]*(fac(tor)?|impl(em)?e?n?t?)'
					r'(e?[ds]?|ing)?'
					r')\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'3-3', self.cat_test, [re.compile(
					r'('
					r'🔬|🧪|⚗️|✅|🦺'
					r'|:test_tube:|:alembic:'
					r'|:white_check_mark:|:safety_vest:'
					r'|te?st(e?[ds]?|ing)?\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'3-4', self.cat_style, [re.compile(
					r'('
					r'🎨|:art:'
					r'|(cd|code)?[^a-zA-Z0-9]*(fo?r?ma?t|sty?le?)(e?[ds]?|ing)?\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'3-5', self.cat_build, [re.compile(
					r'('
					r'📦|:package:'
					r'|bu?i?ld(s|ing)?\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'3-6', self.cat_ci, [re.compile(
					r'('
					r'🤖|👷|:construction_worker:'
					r'|c[id]\b'
					r')'
				).pattern],
			),
			self.__format_single_group_parsers(
				'3-7', self.cat_chore, [re.compile(
					r'('
					r'🧹|🙈|💸|:see_no_evil:|:money_with_wings:'
					r'|('
					r'cho?re?|clean(up)?'
					r'|maint[ae]i?n([ae]n?ce)?'
					r'|git(hub|ignore|att?ri?b?u?t?e?s?)?'
					r')\b'
					r')'
				).pattern],
			),

			"""
# Order-9
# Always last
			""".rstrip().splitlines(),

			self.__format_single_group_parsers(
				'9-2', self.cat_version, [re.compile(
					r'('
					r'🔖|🏷️|🏷|:bookmark:|:label:'
					r'|('
					r'v(er)?[^a-zA-Z0-9]*[0-9]+'
					r'|ver(sion)?'
					r'|bump|release'
					r')\b'
					r')'
				).pattern],
				custom_header_comment=(
					"Version-related changes:\n"
					"Caught BEFORE the catch-all, inserted after"
				),
			),
			self.__format_single_group_parsers(
				'9-1', '🔀 Changes',
				custom_header_comment=(
					"Catch-all:\n"
					"Everything else (uncategorized commits / PR merges).\n"
					"Internal group name is hard-coded, and the actual "
					"title is used later in the template, depending on "
					"the presence of other (properly classified) categories"
				),
				custom_pre_format=[
					'{{ message = ".*", group = {gr} }},'
				],
			),
		)

		indent = '  '
		return chain(
			('commit_parsers = [', ),
			(
				'' if not ln.strip() else f'{indent}{ln}'
				for ln in parser_lines
			),
			']',
		)

	def _format_git_section(self) -> _t.Iterable[str]:
		lines = """
[git]
filter_unconventional = false
sort_commits = "oldest"
topo_order_commits = true
protect_breaking_commits = true
# This ^ prevents commits with `breaking = true` from being suppressed by any `{ ..., skip = true }` parser.
# Skips aren't used in this template yet, but let's have it just as a fail-safe for the future.
		""".strip().splitlines()
		return chain(
			lines,
			[''],
			self.__format_git_commit_parsers(),
		)

	def _format_github_section(self) -> list[str]:
		owner_repr = toml_repr(self.github_owner)
		repo_repr = toml_repr(self.github_repo)
		return f"""
[remote.github]
owner = {owner_repr}
repo = {repo_repr}
		""".strip().splitlines()

	def _format_changelog_section(self) -> list[str]:
		lines_str = r'''
[changelog]
trim = true
header = ""
footer = ""
body = """
{%- set grouped = commits | group_by(attribute="group") -%}
{%- set has_specific = false -%}
{%- for g, gc in grouped -%}
  {%- set dg = g | striptags | trim | upper_first -%}
  {%- if dg != "🔀 Changes" and dg != "${{ inputs.cat-version }}" -%}
    {%- set_global has_specific = true -%}
  {%- endif -%}
{%- endfor -%}
{%- for group, commits in grouped -%}
{%- set display_group = group | striptags | trim | upper_first -%}
{%- set_global alert_type = "" -%}
{%- set_global alert_indent = "" -%}${{ PUT_ALERT_TEMPLATE_LINES_HERE }}
{% if display_group == "🔀 Changes" -%}
  {%- if has_specific -%}
  {{ alert_indent }}## ${{ inputs.cat-unclassified-multi }}
  {%- else -%}
  {{ alert_indent }}## ${{ inputs.cat-unclassified-only }}
  {%- endif -%}
{% else -%}
  {{ alert_indent }}## {{ display_group }}
{%- endif %}
{{ alert_indent }}
{% for commit in commits %}
{%- set msg = commit.message | trim -%}
{%- set title = msg | split(pat="\n") | first | trim -%}
{%- set cbody = msg | split(pat="\n") | slice(start=1) | join(sep="\n") | trim -%}
{%- set sha7 = commit.id | truncate(length=7, end="") -%}
{%- set who = commit.remote.username | default(value=commit.author.name) -%}
{{ alert_indent }}- {% if commit.remote.pr_number -%}
{{ commit.remote.pr_title | default(value=title) }} — #{{ commit.remote.pr_number }} by @{{ who }}
{%- else -%}
{{ title }} — {{ commit.id }} by @{{ who }}
{%- if cbody %}
{{ alert_indent ~ "  > " ~ cbody | replace(from="\n", to="\n" ~ alert_indent ~ "  > ") }}
{%- endif %}
{%- endif %}
{% endfor %}
{% endfor %}
"""
		'''.strip()

		alert_template_lines = '\n' + r"""
{%- if display_group == "${{ inputs.cat-breaking }}" -%}
  {%- set_global alert_type = "CAUTION" -%}
  {%- set_global alert_indent = "> " -%}
{%- elif display_group == "${{ inputs.cat-depr }}" -%}
  {%- set_global alert_type = "WARNING" -%}
  {%- set_global alert_indent = "> " -%}
{%- elif display_group == "${{ inputs.cat-revert }}" -%}
  {%- set_global alert_type = "IMPORTANT" -%}
  {%- set_global alert_indent = "> " -%}
{%- endif -%}
{%- if alert_type != "" -%}
> [!{{ alert_type }}]
{% endif -%}
		""".strip()
		if not self.cat_alert_blocks:
			alert_template_lines = ''

		lines_str = lines_str.replace('${{ PUT_ALERT_TEMPLATE_LINES_HERE }}', alert_template_lines)

		# Since the template itself contains A TON of curly braces,
		# let's put the values with simple replace instead of format:
		# noinspection PyTypeChecker
		instance_dict = asdict(self)
		for attr_name, value in instance_dict.items():
			github_input = attr_name.replace('_', '-')
			github_expr = '${{ inputs.' + github_input + ' }}'
			value_str = toml_repr(str(value), dont_wrap_in_quotes=True)
			lines_str = lines_str.replace(github_expr, value_str)

		return lines_str.splitlines()

	@staticmethod
	def __join_sections(*sections: _t.Iterable[str], sep=('',)) -> _t.Iterable[str]:
		sec_iter = iter(sections)
		try:
			first_section = next(sec_iter)
		except StopIteration:
			return []

		new_sections: list[_t.Iterable[str]] = [first_section, ]
		for sec in sec_iter:
			new_sections.append(iter(sep))  # new iterator each time
			new_sections.append(sec)
		return chain(*new_sections)

	def lines(self) -> list[str]:
		"""The code of generated config as list of lines (``\\n`` in the end)."""
		return list(self.__join_sections(
			self._format_git_section(),
			self._format_github_section(),
			self._format_changelog_section(),
			[''],
		))


def main(fallback_out_file='cliff.just-release-it.toml') -> None:
	# To protect from bash code-injection attacks in GitHub action,
	# it's MUCH safer to pass all the necessary values as env-vars,
	# rather than as script args.
	# So, retrieve them:
	kwargs = {
		nm: cleanup_as_single_line(os.environ.get(nm)) for nm in [
			'cat_alert_blocks',

			'cat_breaking',
			'cat_depr',
			'cat_revert',
			'cat_feat',
			'cat_enhance',
			'cat_fix',
			'cat_perf',
			'cat_security',
			'cat_doc',
			'cat_refactor',
			'cat_test',
			'cat_style',
			'cat_build',
			'cat_ci',
			'cat_chore',
			'cat_version',
			'cat_unclassified_multi',
			'cat_unclassified_only',

			'github_owner',
			'github_repo',

			'out_config_file',
		]
	}

	# String-boolean values have to be processed before filtering out:
	try:
		cat_alert_blocks_str = kwargs.pop('cat_alert_blocks')
	except KeyError:
		cat_alert_blocks_str = str(ConfigGenerator.cat_alert_blocks)
	cat_alert_blocks_bool = is_true_str(cat_alert_blocks_str)

	# Now, filer out any unset strings to fall back to defaults:
	kwargs = {k: v for k, v in kwargs.items() if v}

	# ... and restore the actual bool values:
	# noinspection PyTypeChecker
	kwargs['cat_alert_blocks'] = cat_alert_blocks_bool

	try:
		out_config_file = kwargs.pop('out_config_file')
	except KeyError:
		out_config_file = cleanup_as_single_line(fallback_out_file)

	config_lines = ConfigGenerator(**kwargs).lines()

	with open(out_config_file, 'wt', encoding='utf-8') as f:
		f.writelines(f'{ln}\n' for ln in config_lines)

	print(f"cliff-config saved: {out_config_file}\n")
	for ln in config_lines:
		print(ln)


if __name__ == '__main__':
	main()
