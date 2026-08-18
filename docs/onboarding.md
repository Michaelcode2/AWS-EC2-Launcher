# Customer onboarding

EC2 Desktop Manager is a Windows desktop client. **AWS IAM is the
authorization boundary.** A local TOML profile only controls what the
application shows. It cannot grant Start, Stop, or Restart.

You need two things before the first sign-in:

1. An **AWS CLI named profile** with credentials (IAM user access keys, or
   IAM Identity Center SSO).
2. An **application TOML profile** (account, region, filters, feature flags).
   `[aws] profile` in the TOML file must match the CLI profile name.

Never store secret keys, session tokens, or Windows passwords in the TOML file.
Access keys belong in `%USERPROFILE%\.aws\credentials` only.

## Prerequisites

- Windows 10/11 x64
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  (needed to create the named profile; SSO sign-in also uses it)
- An IAM principal that can call `ec2:DescribeInstances` plus the actions you
  intend to expose (see `docs/iam-desktop-policy.json`)

Confirm the CLI is v2:

```powershell
aws --version
```

The output must start with `aws-cli/2`.

## 1. Create the AWS CLI profile

### Regular AWS account (IAM user)

Create an IAM user with programmatic access and attach a least-privilege
policy (start from `docs/iam-desktop-policy.json`). Then:

```powershell
aws configure --profile customer-server
```

Enter:

| Prompt | Example |
| --- | --- |
| AWS Access Key ID | `AKIA...` |
| AWS Secret Access Key | the secret for that key |
| Default region name | `eu-central-1` |
| Default output format | `json` |

This writes `%USERPROFILE%\.aws\credentials` and `.aws\config`. Do not paste
those keys into the application TOML file.

If you already use the default CLI profile, you can keep it and set
`[aws] profile = "default"` in the application file.

Test before opening the app:

```powershell
aws sts get-caller-identity --profile customer-server
```

`Account` in the JSON is the 12-digit ID for `expected_account_id`.

### IAM Identity Center (SSO)

If the account uses Identity Center instead of long-term keys:

```powershell
aws configure sso
```

Typical prompts: start URL, SSO region, account, permission set, CLI region,
and profile name. Then:

```powershell
aws sso login --profile customer-server
aws sts get-caller-identity --profile customer-server
```

## 2. Create the application profile

Copy `config/example-profile.toml` to the user config directory and edit it.

Installed app:

```text
%LOCALAPPDATA%\Ec2DesktopManager\config\
```

Running from source on this machine, that is typically:

```text
C:\Users\<you>\AppData\Local\Ec2DesktopManager\config\
```

From source the app also loads `config\` in the repository, including the
example file. For a real account, put a TOML file in the user directory so
you do not edit the example in git.

Minimal file (`my-customer.toml`):

```toml
[application]
name = "My Customer"
expected_account_id = "123456789012"
default_region = "eu-central-1"
refresh_interval_seconds = 15
confirm_start = false

[aws]
profile = "customer-server"

[filters]
mode = "all"

[rdp]
enabled = true
use_elastic_ip = true
check_readiness = false

[features]
allow_start = true
allow_stop = true
allow_restart = true
```

Required fields:

- `application.name` — label in the login dropdown
- `application.expected_account_id` — 12-digit AWS account ID
- `application.default_region` — region used for EC2 calls
- `aws.profile` — exact AWS CLI profile name from step 1

Optional filters (`all`, `instance_ids`, or `tags`):

```toml
[filters]
mode = "tags"

[filters.tags]
ManagedBy = "ec2-desktop-manager"
```

or:

```toml
[filters]
mode = "instance_ids"
instance_ids = ["i-0123456789abcdef0"]
```

Set `allow_start` / `allow_stop` / `allow_restart` to `false` to hide those
buttons. That only hides UI; IAM still decides what AWS allows.

## 3. First sign-in in the app

From source (no Nuitka build required):

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\ec2-desktop-manager.exe
```

Or start the installed **EC2 Desktop Manager**.

1. Select the customer profile in the dropdown.
2. Choose **Sign in**.
3. For an IAM user profile the app uses the keys already in
   `%USERPROFILE%\.aws\credentials`. For SSO it opens the AWS CLI browser
   login. Do not type an AWS console password into this application.
4. The main window opens only if STS `GetCallerIdentity` matches
   `expected_account_id`.

If login fails:

- the CLI profile name in TOML does not exist (`aws configure --profile ...`)
- access key / secret is wrong or missing
- for SSO: AWS CLI v2 is missing, or browser sign-in was cancelled
- the signed-in account ID does not match `expected_account_id`

## Idle auto-stop

The desktop client does not stop idle instances. Install
`scripts/idle-stop/` on the Windows EC2 instance itself. See
`scripts/idle-stop/README.md`.
