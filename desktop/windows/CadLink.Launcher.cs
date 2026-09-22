// SPDX-License-Identifier: LGPL-3.0-or-later
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Windows.Forms;

namespace CadLink
{
    [DataContract]
    public sealed class LauncherConfiguration
    {
        [DataMember(Name = "allowedRoots", IsRequired = true)]
        public string[] AllowedRoots { get; set; }
    }

    public static class Launcher
    {
        [STAThread]
        public static int Main(string[] args)
        {
            bool checkOnly = args.Length == 2 && args[0] == "--check";
            try
            {
                // Registry invokes this EXE directly. Extra command-line arguments
                // are rejected; a URI is never interpreted by cmd or PowerShell.
                if (args.Length != 1 && !checkOnly)
                    throw new ArgumentException("CAD-link expects exactly one request.");
                string configPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
                if (new FileInfo(configPath).Length > 65536)
                    throw new IOException("The CAD-link configuration is too large.");
                LauncherConfiguration configuration;
                using (FileStream stream = File.OpenRead(configPath))
                {
                    var serializer = new DataContractJsonSerializer(typeof(LauncherConfiguration));
                    configuration = (LauncherConfiguration)serializer.ReadObject(stream);
                }
                LaunchRequest request = RequestParser.Parse(args[checkOnly ? 1 : 0], configuration.AllowedRoots);
                FileAttributes attributes = TargetValidator.Check(request);
                if (checkOnly)
                {
                    Console.WriteLine("CAD-link request validated; no application launched.");
                    Console.WriteLine("Action: " + request.Action);
                    Console.WriteLine("Path: " + request.Path);
                    Console.WriteLine("Directory: " + ((attributes & FileAttributes.Directory) != 0));
                    return 0;
                }
                ProcessStartInfo start;
                if (request.Action == "open")
                {
                    start = new ProcessStartInfo(request.Path);
                    start.UseShellExecute = true;
                    start.Verb = "open";
                }
                else
                {
                    string explorer = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.Windows), "explorer.exe");
                    // Quotes/control characters have already been rejected. No shell.
                    string quotedPath = "\"" + request.Path + "\"";
                    start = new ProcessStartInfo(explorer,
                        (attributes & FileAttributes.Directory) != 0
                            ? quotedPath : "/select," + quotedPath);
                    start.UseShellExecute = false;
                }
                Process.Start(start);
                return 0;
            }
            catch (Exception error)
            {
                if (checkOnly)
                    Console.Error.WriteLine("CAD-link validation failed: " + error.Message);
                else
                    MessageBox.Show("The network document could not be opened.\n\n" + error.Message,
                        "CAD-link", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return 1;
            }
        }
    }
}
