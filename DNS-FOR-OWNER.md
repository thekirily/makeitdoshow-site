# Email setup for the owner — 2026-11-07

Recommend **Brevo Free** for the first 100 visitors. Its hosted Simple HTML form supports double confirmation without exposing an API key or adding a remote script. The 300-email daily cap must cover confirmation, welcome and campaign sends combined; 100 people with confirmation + welcome can use roughly 200 sends. Do not enable capture until sender authentication and actual inbox tests pass.

## Three free services, checked against current primary sources

| Service | Free capacity | Double opt-in and API | Deliverability evidence and GDPR terms |
|---|---|---|---|
| **Brevo** | 100,000 stored contacts; 300 sends/day; automation up to 2,000 contacts | Hosted forms offer Double confirmation; REST marketing/transactional API. The implementation uses the hosted form, so no API secret is needed in the page. | Publishes domain-authentication and anti-spam guidance; shared sending reputation still depends on the sender/list. DPA is in its service terms. No inbox percentage is claimed here. |
| MailerLite | 250 subscribers; 2,500 sends/month on the current free page | Form DOI; separate API/integrations DOI setting. REST API; free API access is limited and excludes email sending. | Domain authentication and list controls; free DOI-email customization is restricted. DPA includes EU/UK transfer provisions. No measured reputation comparison for this domain exists. |
| EmailOctopus | 2,500 subscribers; 10,000 sends/month; one form/landing page; 30-day reports | DOI must be enabled: default is single opt-in. Contacts/campaign API. | Domain verification sets authentication; provider says subscriber data are stored in Ireland. Data-processing schedule in terms. Inbox placement for this new domain is untested. |

Sources: Brevo [free limits](https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans), [form/DOI](https://help.brevo.com/hc/en-us/articles/208771869-Create-a-sign-up-form-in-Brevo), [API](https://developers.brevo.com/), [terms/DPA](https://www.brevo.com/legal/termsofuse/); MailerLite [pricing](https://www.mailerlite.com/pricing), [DOI](https://www.mailerlite.com/help/how-to-use-double-opt-in-when-collecting-subscribers), [API](https://developers.mailerlite.com/guides), [DPA](https://www.mailerlite.com/legal/data-processing-agreement); EmailOctopus [pricing](https://emailoctopus.com/pricing), [DOI](https://help.emailoctopus.com/article/36-how-to-edit-double-opt-in), [API](https://help.emailoctopus.com/article/94-api-documentation), [storage](https://help.emailoctopus.com/article/8-data-storage-and-gdpr-compliance), [terms](https://emailoctopus.com/legal/terms). Limits can change; verify again when opening the account.

Provider reputation is not this domain's deliverability. No seeds, messages, mailbox accounts or authenticated sender were available to measure inbox placement. No account was opened, paid plan selected or email sent.

## DNS: exact known values and the account-specific blocker

Read-only public DNS checks are retained in `evidence/launch-1107/dns.json`. At audit time the apex had no TXT/SPF or MX answers, `_dmarc.makeitdoshow.com` was NXDOMAIN, and `mail.makeitdoshow.com` had no TXT answer. DNS cache results are observations, not authority to overwrite later records. No DNS was changed.

Use an owner-controlled From address, for example `updates@makeitdoshow.com`, with a working Reply-To mailbox. The current `chaddoto2@gmail.com` can remain support, but the owner cannot authenticate `gmail.com` in Brevo. A mailbox/forwarding provider is a separate owner choice; do not promise that `updates@` receives replies until configured.

| Purpose | Type / fully qualified name | Value / exactness | TTL |
|---|---|---|---:|
| DMARC initial monitoring | TXT `_dmarc.makeitdoshow.com` | **Exact deployable value:** `v=DMARC1; p=none; adkim=r; aspf=r` | 3600 |
| Brevo ownership | TXT at the exact host shown by Brevo (normally `makeitdoshow.com`) | **Blocked:** `brevo-code:<account-generated-code>`; copy the literal code from this account. The placeholder is not a valid record. | 3600 |
| DKIM | The one TXT selector or two CNAME selectors shown by this account's Brevo setup | **Blocked:** copy both the exact selector hostname(s) and public key/CNAME target(s). They are generated for the account/domain; no universal values exist. | 3600 |
| SPF for Brevo Free shared sending | Provider-controlled envelope sender | **No apex SPF addition is required for the standard shared setup.** Brevo authenticates its own Return-Path; aligned DKIM supplies DMARC alignment. Do not paste a speculative `include:spf.brevo.com` into this domain. | — |
| SPF for an owner mailbox/custom Return-Path | TXT at the sending hostname specified by the chosen provider | **Blocked by mailbox/Return-Path choice.** Merge the provider's exact mechanism into one existing SPF record; never create two `v=spf1` records at one host. | 3600 |

[Brevo's current authentication instructions](https://help.brevo.com/hc/en-us/articles/12163873383186-Authenticate-your-domain-with-Brevo-Brevo-code-DKIM-DMARC) explain the account-specific Brevo code, TXT/CNAME DKIM alternatives, DMARC, and why standard SPF/MX changes are not required for authentication. Its new guided setup may issue different record shapes. Use those issued values. An invented DKIM key would make this document look complete while leaving mail unauthenticated.

The exact account-specific DNS set cannot be completed without an account/domain setup. The deliverable is therefore **partial / blocked**, not DNS-ready. Owner: open or select the account, obtain the generated public records, and have the DNS operator apply them. Keep API keys/passwords in local environment or provider settings; never paste them into chat, HTML, Git or audit screenshots.

After a receiving mailbox for aggregate reports exists, replace the single DMARC record with `v=DMARC1; p=none; adkim=r; aspf=r; rua=mailto:dmarc@makeitdoshow.com` only if that mailbox is monitored. Review reports before the owner changes policy to quarantine/reject. The initial monitoring policy does not block spoofed mail. Gumroad receipts authenticate Gumroad's domain; changing this domain's SPF cannot repair Gumroad receipt spam placement.

## Enable the already-built form

1. In Brevo select the free plan, verify the sender/domain, create a list and a sign-up form using **Double confirmation**, and configure a custom post-submit page for Simple HTML compatibility. The form endpoint enforces DOI; a local boolean does not configure Brevo.
2. Copy the action URL from its **Simple HTML** export into `data/site.json → email_capture.form_action`. Preserve the standard `EMAIL`, `OPT_IN`, `locale`, `html_type` and honeypot field contract. If the account export differs, reconcile the fields before enabling. Do not add Brevo's remote embed script.
3. Inspect both the DOI email and confirmed welcome email in Brevo. Add an honest sender name, reply address, postal address, unsubscribe, and privacy link. Disable open/click tracking unless separately reviewed and disclosed. Free download access stays independent of marketing consent.
4. Verify real confirmation/unsubscribe with owner seed addresses in Gmail, Outlook and Yahoo. Check headers: SPF pass on Return-Path, DKIM pass with aligned `d=makeitdoshow.com`, DMARC pass, correct links and mobile rendering. Confirm pending people do not receive campaigns. These tests have not been performed here.
5. Set `double_opt_in_verified=true` and `enabled=true`, build, run `python3 tests/signup_smoke.py`, and review before owner publication. The form appears on home; it works as a native POST without JavaScript. Build refuses an unapproved host, missing endpoint or missing DOI attestation. CSP admits only that exact form origin.

The six signup smoke checks use an intercepted fixture endpoint and send no mail. `signup_started` means a form submission attempt; a return URL cannot prove DOI. Confirmed Brevo subscribers are counted in Brevo's DOI/list records. There is no authenticated Brevo→PostHog confirmation bridge in this PR, so do not use browser submissions as confirmed email conversions. Existing `signup_completed` remains reserved for authenticated free Gumroad transactions.
