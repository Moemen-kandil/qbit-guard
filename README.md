# 🛡️ qbit-guard - Protect Your Downloads Effortlessly

## 🚀 Getting Started

Welcome to qbit-guard! This guide will help you download and run our software. qbit-guard is a zero-dependency Python application designed to keep your qBittorrent downloads safe and organized. It blocks unwanted pre-air TV episodes, removes unnecessary ISO/BDMV-only torrents, and maintains a smart blocklist to filter out bad releases.

## 📥 Download qbit-guard

[![Download qbit-guard](https://img.shields.io/badge/Download%20Now%20-via%20GitHub-blue.svg)](https://github.com/Moemen-kandil/qbit-guard/releases)

To get started, you need to visit our Releases page to download the latest version of qbit-guard. Click the link below to access it:

[Download the latest version](https://github.com/Moemen-kandil/qbit-guard/releases)

## 📋 Features

Here are some of the key features of qbit-guard:

- **Pre-Air TV Blocking:** Automatically blocks episodes from shows before they officially air.
- **Torrent Cleanup:** Deletes ISO/BDMV-only torrents that clutter your library.
- **Auto-Blocklist Management:** Integrates with Sonarr and Radarr to manage bad releases.
- **Safe Metadata Fetching:** Gathers metadata without compromising your privacy.
- **Comprehensive Logging:** Outputs logs to the console for easy tracking of activity.

## 💻 System Requirements

To run qbit-guard smoothly, your system should meet the following requirements:

- Operating System: Windows, macOS, or Linux
- Python Version: Python 3.6 or later installed on your machine (if not included)
- Minimum Storage: 50 MB of free space
- Internet Connection: Required for downloading metadata and fetching updates

## 🛠️ Installation Steps

### Step 1: Download the Software

1. Go to the [Releases page](https://github.com/Moemen-kandil/qbit-guard/releases).
2. Find the latest version of qbit-guard.
3. Click the file that corresponds to your operating system to start downloading.

### Step 2: Install (If Necessary)

Most users can run qbit-guard directly without installation. If you need to install Python, follow these instructions:

1. Download Python from the [official Python website](https://www.python.org/downloads/).
2. Run the installer and follow the prompts.
3. Make sure to check "Add Python to PATH" during installation.

### Step 3: Run qbit-guard

1. Open your command line interface (Terminal on macOS/Linux, Command Prompt or PowerShell on Windows).
2. Navigate to the folder where you downloaded qbit-guard. Use the `cd` command to change directories. For example:
   - Windows: `cd Downloads`
   - macOS/Linux: `cd ~/Downloads`
3. Run qbit-guard by typing the following command:
   ```
   python qbit-guard.py
   ```

## 🔍 Configuration Options

qbit-guard offers some settings to help you customize its functionality. You can adjust these options in a configuration file. 

### Example Configurations:

- **Blocklist URL:** Specify a custom URL where undesirable torrents can be fetched.
- **Logging Level:** Choose your logging preferences for console output, such as INFO, WARNING, or ERROR.

## 📊 Usage

Once you have qbit-guard running, it automatically listens for new torrents added to qBittorrent. The application checks the incoming torrents, comparing them against its criteria for blocking or deleting. You will see log messages in the console, detailing which torrents it has acted on.

## 📃 Troubleshooting

If you encounter any issues, here are some common problems and solutions:

- **Python Not Found:** Ensure Python is installed and added to your PATH.
- **Dependencies Missing:** qbit-guard is designed to have zero dependencies, but if there's an error, verify your Python version.
- **Logs Not Outputting:** Check the console window for any error messages that can guide you to the issue.

## 🛡️ Support

If you need further assistance, please visit our issues page on GitHub to report problems or ask questions. We aim to respond swiftly and help you get back on track.

## 📖 Additional Resources

- [GitHub Repository](https://github.com/Moemen-kandil/qbit-guard)
- [qBittorrent Website](https://www.qbittorrent.org)

## 📥 Final Download Reminder

Don’t forget to grab your copy of qbit-guard from our Releases page. Click below to download:

[Download the latest version](https://github.com/Moemen-kandil/qbit-guard/releases)