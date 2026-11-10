#if !SWITCH
// PC platform layer (play-test campaign Phase 5, HANDOFF §11.7 / §11.14): NOT shipped code. The shipped game calls the Switch SDK
// through `extern` declarations in nn/, Dpr/NX/, RestartUtility, PlayReportEvent, SwitchNativeUtils ...; on PC each of those
// declarations is `#if SWITCH extern ... #else { PC body } #endif` (author decision D3 (a)) and the PC bodies call into this folder.
// Game files are not edited.
using System;
using System.IO;
using UnityEngine;

namespace PcPlatform
{
    // The emulated console: one user account, the Ryujinx default profile, so a save written here is the save Ryujinx reads
    // (HANDOFF §11.10 PM4 - the same game state on both sides).
    public static class PcConfig
    {
        // Ryujinx AccountManager.DefaultUserId = new UserId("00000000000000010000000000000000") = High 1, Low 0 (reference tree 475615f,
        // Ryujinx.HLE/HOS/Services/Account/Acc/AccountManager.cs l.17); UserId.Write puts High first, so the guest's
        // nn::account::Uid is {_data[0] = 1, _data[1] = 0}. Name "RyuPlayer". (s33 had Low = 1 - corrected in Phase 6, HANDOFF §11.15.)
        public static ulong UserId0 = 0x0000000000000001UL;
        public static ulong UserId1 = 0x0000000000000000UL;
        public static string Nickname = "RyuPlayer";

        // The console time zone = the host's (the game reads System.DateTime.Now directly, which Mono answers in the Windows zone):
        // the tz database name + abbreviation of the author's Windows zone "SE Asia Standard Time". The reference emulator MUST run with
        // --system-timezone <TimeZoneLocation> (tools/ryubing_run.py does), or the two in-game clocks differ by the zone offset.
        public static string TimeZoneLocation = "Asia/Bangkok";
        public static string TimeZoneAbbreviation = "+07";

        public static bool IsShiningPearl { get; private set; }
        public static int CassetVersion => IsShiningPearl ? global::CassetVersion.DPR_S : global::CassetVersion.DPR_B;
        public static byte RomCode => (byte)(IsShiningPearl ? 1 : 0);
        // The save directory is keyed by the title ID of the exported edition.
        public static ulong ApplicationId => IsShiningPearl ? 0x010018E011D92000UL : 0x0100000011D90000UL;

        public static void ConfigureEdition(string buildVersion)
        {
            switch (buildVersion)
            {
                case "delphis_MS075493D_m19820_v1_3_0":
                    IsShiningPearl = false;
                    break;
                case "delphis_MS075493P_m19820_v1_3_0":
                    IsShiningPearl = true;
                    break;
                default:
                    throw new InvalidOperationException("Unsupported StartupSettings build version: " + buildVersion);
            }
            Log(IsShiningPearl ? "Shining Pearl v1.3.0" : "Brilliant Diamond v1.3.0");
        }

        static string _root;

        // <persistentDataPath>/nn - everything the emulated SDK stores (save data, ...).
        public static string Root
        {
            get
            {
                if (_root == null)
                {
                    _root = Path.Combine(Application.persistentDataPath, "nn");
                    Directory.CreateDirectory(_root);
                }
                return _root;
            }
        }

        public static void Log(string message)
        {
            UnityEngine.Debug.Log("[PcPlatform] " + message);
        }
    }

    // nn::Abort ends the process on the console; in the editor it becomes an exception the play log records with its stack.
    public class NnAbortException : Exception
    {
        public NnAbortException(string message) : base("nn::Abort: " + message) { }
    }

    // A Switch SDK entry point the PC layer does not implement (never reached on the play-test route so far). Loud on purpose.
    public static class Unsupported
    {
        public static Exception Api(string api)
        {
            return new NotSupportedException("[PcPlatform] Switch API not available on PC: " + api);
        }
    }
}
#endif
