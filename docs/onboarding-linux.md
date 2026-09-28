# Customer onboarding (Linux)

EC2 Desktop Manager is available on Linux as a standalone AppImage.
**AWS IAM is the authorization boundary.** A local TOML profile only
controls what the application shows. It cannot grant Start, Stop, or Restart.

You need two things before the first sign-in:

1. An **AWS CLI named profile** with credentials (IAM user access keys, or
   IAM Identity Center SSO).
2. An **application TOML profile** (account, region, filters, feature flags).
   `[aws] profile` in the TOML file must match the CLI profile name.

Never store secret keys, session tokens, or Windows passwords in the TOML file.
Access keys belong in `~/.aws/credentials` only.

For Windows workstations, see `docs/onboarding.md`.

## Prerequisites

- Ubuntu Desktop 22.04 or 24.04, KDE Plasma on those Ubuntu bases, or
  Linux Mint 21 or 22 (x86_64)
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  (needed to create the named profile; SSO sign-in also uses it)
- A FreeRDP client if you use **Connect RDP** (`freerdp2-x11` or
  `freerdp3-x11`)
- An IAM principal that can call `ec2:DescribeInstances` plus the actions you
  intend to expose (see `docs/iam-desktop-policy.json`)

Confirm the CLI is v2:

```bash
aws --version
```

The output must start with `aws-cli/2`.

Install FreeRDP when you need RDP from the app:

```bash
# Ubuntu 22.04 / Linux Mint 21 (typical)
sudo apt install freerdp2-x11

# Ubuntu 24.04 / Linux Mint 22 (typical)
sudo apt install freerdp3-x11
```

The app looks on `PATH` for `xfreerdp`, then `xfreerdp3`, then `wlfreerdp`.

## 1. Create the AWS CLI profile

### Regular AWS account (IAM user)

Create an IAM user with programmatic access and attach a least-privilege
policy (start from `docs/iam-desktop-policy.json`). Then:

```bash
aws configure --profile customer-server
```

Enter:

| Prompt | Example |
| --- | --- |
| AWS Access Key ID | `AKIA...` |
| AWS Secret Access Key | the secret for that key |
| Default region name | `eu-central-1` |
| Default output format | `json` |

This writes `~/.aws/credentials` and `~/.aws/config`. Do not paste those keys
into the application TOML file.

If you already use the default CLI profile, you can keep it and set
`[aws] profile = "default"` in the application file.

Test before opening the app:

```bash
aws sts get-caller-identity --profile customer-server
```

`Account` in the JSON is the 12-digit ID for `expected_account_id`.

### IAM Identity Center (SSO)

If the account uses Identity Center instead of long-term keys:

```bash
aws configure sso
```

Typical prompts: start URL, SSO region, account, permission set, CLI region,
and profile name. Then:

```bash
aws sso login --profile customer-server
aws sts get-caller-identity --profile customer-server
```

## 2. Create the application profile

Copy `config/example-profile.toml` to the user config directory and edit it.

AppImage / first launch:

```text
~/.local/share/Ec2DesktopManager/config/
```

If `XDG_DATA_HOME` is set, profiles live under:

```text
$XDG_DATA_HOME/Ec2DesktopManager/config/
```

On first launch with an empty config directory, the AppImage copies the
shipped example profile into that folder. For a real account, edit that file
or add your own `*.toml` so you do not rely on the example values.

From a source checkout the app also loads `config/` in the repository,
including the example file. Prefer the user directory for a live account.

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

## 3. Get and launch the AppImage

Download `EC2DesktopManager-*-x86_64.AppImage` from the GitHub Actions
`build-linux` workflow artifact. Make it executable:

```bash
chmod +x EC2DesktopManager-*.AppImage
```

Type-2 AppImages need FUSE 2. Install it, or use extract-and-run:

```bash
# Ubuntu 22.04 / Linux Mint 21
sudo apt install libfuse2

# Ubuntu 24.04 / Linux Mint 22 (package name may be libfuse2t64)
sudo apt install libfuse2t64
```

```bash
./EC2DesktopManager-*.AppImage
# or, without FUSE:
APPIMAGE_EXTRACT_AND_RUN=1 ./EC2DesktopManager-*.AppImage
```

Optional per-user application menu entry (no administrator rights):

```bash
./EC2DesktopManager-*.AppImage --install-desktop-entry
```

That writes `~/.local/share/applications/ec2-desktop-manager.desktop` and an
icon under `~/.local/share/icons/`.

### From source (developers)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
ec2-desktop-manager
```

## 4. First sign-in in the app

1. Select the customer profile in the dropdown.
2. Choose **Sign in**.
3. For an IAM user profile the app uses the keys already in
   `~/.aws/credentials`. For SSO it opens the AWS CLI browser login. Do not
   type an AWS console password into this application.
4. The main window opens only if STS `GetCallerIdentity` matches
   `expected_account_id`.

**Connect RDP** starts FreeRDP against the same address selection as Windows
(`mstsc.exe` there). The application never stores or injects a Windows
password; authenticate in the FreeRDP prompt.

If login fails:

- the CLI profile name in TOML does not exist (`aws configure --profile ...`)
- access key / secret is wrong or missing
- for SSO: AWS CLI v2 is missing, or browser sign-in was cancelled
- the signed-in account ID does not match `expected_account_id`

If Connect RDP fails:

- FreeRDP is not installed (`xfreerdp` / `xfreerdp3` / `wlfreerdp` not on `PATH`)
- the instance is not `running`, or the optional readiness check failed
- network or security group blocks TCP 3389 to the Elastic IP / public IP

## Idle auto-stop

The desktop client does not stop idle instances. Install
`scripts/idle-stop/` on the Windows EC2 instance itself. See
`scripts/idle-stop/README.md`.
