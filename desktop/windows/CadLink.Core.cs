// SPDX-License-Identifier: LGPL-3.0-or-later
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

namespace CadLink
{
    public sealed class LaunchRequest
    {
        public string Action { get; private set; }
        public string Path { get; private set; }

        public LaunchRequest(string action, string path)
        {
            Action = action;
            Path = path;
        }
    }

    // No I/O during parsing: reject untrusted URIs before touching the network.
    public static class RequestParser
    {
        private static readonly Regex UriPattern = new Regex(
            @"\Acad-link://(open|folder)/?\?path=((?:[A-Za-z0-9._~!'()*-]|%[0-9A-Fa-f]{2})+)\z",
            RegexOptions.CultureInvariant);
        private static readonly Regex ServerPattern = new Regex(
            @"\A[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\z",
            RegexOptions.CultureInvariant);
        private static readonly Regex DeviceName = new Regex(
            @"\A(?:CON|PRN|AUX|NUL|COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3])(?:\..*)?\z",
            RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
        private static readonly HashSet<string> Extensions = new HashSet<string>(
            new string[] { ".ipt", ".iam", ".idw", ".dwg", ".dxf", ".pdf",
                ".step", ".stp", ".iges", ".igs", ".sat", ".stl", ".obj",
                ".mtl", ".glb", ".gltf" }, StringComparer.OrdinalIgnoreCase);

        public static string ValidateUncPath(string path)
        {
            // Stay below legacy Win32 MAX_PATH. Long-path support varies by CAD app.
            if (String.IsNullOrEmpty(path) || path.Length > 259 ||
                !path.StartsWith(@"\\", StringComparison.Ordinal))
                throw new ArgumentException("Use a UNC path below 260 characters.");
            if (path.IndexOfAny(new char[] { '/', ':', '"', '<', '>', '|', '?', '*' }) >= 0)
                throw new ArgumentException("The network path contains a forbidden character.");
            foreach (char character in path)
                if (Char.IsControl(character) || Char.IsSurrogate(character))
                    throw new ArgumentException("The network path contains an unsupported character.");

            string[] parts = path.Substring(2).Split('\\');
            if (parts.Length < 2 || !ServerPattern.IsMatch(parts[0]) ||
                parts[0].Contains(".."))
                throw new ArgumentException("Use a server name and a share name.");
            foreach (string part in parts)
            {
                if (String.IsNullOrEmpty(part) || part == "." || part == ".." ||
                    part.EndsWith(".", StringComparison.Ordinal) ||
                    part.EndsWith(" ", StringComparison.Ordinal) || DeviceName.IsMatch(part))
                    throw new ArgumentException("The network path has an unsafe component.");
            }
            return path;
        }

        public static bool IsAllowedFile(string path)
        {
            return Extensions.Contains(System.IO.Path.GetExtension(path));
        }

        public static LaunchRequest Parse(string uri, string[] allowedRoots)
        {
            if (String.IsNullOrEmpty(uri) || uri.Length > 8192)
                throw new ArgumentException("Invalid CAD-link request.");
            Match match = UriPattern.Match(uri);
            if (!match.Success)
                throw new ArgumentException("Use a CAD-link open or folder request with one path.");
            string path = ValidateUncPath(Uri.UnescapeDataString(match.Groups[2].Value));
            if (allowedRoots == null || allowedRoots.Length == 0)
                throw new ArgumentException("No allowed network folder is configured.");

            bool allowed = false;
            foreach (string configuredRoot in allowedRoots)
            {
                string root = ValidateUncPath(configuredRoot);
                if (String.Equals(path, root, StringComparison.OrdinalIgnoreCase) ||
                    path.StartsWith(root + @"\", StringComparison.OrdinalIgnoreCase))
                    allowed = true;
            }
            if (!allowed)
                throw new ArgumentException("The requested path is outside the allowed network folders.");
            string action = match.Groups[1].Value;
            if (action == "open" && !IsAllowedFile(path))
                throw new ArgumentException("This file type cannot be opened by CAD-link.");
            return new LaunchRequest(action, path);
        }
    }

    public static class TargetValidator
    {
        public static FileAttributes Check(LaunchRequest request)
        {
            return Check(request, File.GetAttributes);
        }

        public static FileAttributes Check(LaunchRequest request, Func<string, FileAttributes> attributesForPath)
        {
            // Reject visible reparse points at every level, including the share.
            // This is a best-effort check, not a server-side path confinement API.
            string[] parts = request.Path.Substring(2).Split('\\');
            string current = @"\\" + parts[0];
            FileAttributes attributes = 0;
            for (int index = 1; index < parts.Length; index++)
            {
                current += @"\" + parts[index];
                attributes = attributesForPath(current);
                if ((attributes & FileAttributes.ReparsePoint) != 0)
                    throw new IOException("CAD-link does not open junctions or symbolic links.");
            }
            bool isDirectory = (attributes & FileAttributes.Directory) != 0;
            if (request.Action == "open" && isDirectory)
                throw new IOException("Select a document to open, or use Open folder.");
            if (!isDirectory && !RequestParser.IsAllowedFile(request.Path))
                throw new IOException("This file type cannot be opened or selected by CAD-link.");
            return attributes;
        }
    }
}
