// BDSP play-test campaign, D7 (HANDOFF §11.15): editor-only tooling for the native texture rebuild - not game code.
//   BdspD7.WriteTemplate (-executeMethod): writes Assets/_d7_template/d7_template.asset (a 8x8 DXT1 Texture2D with mips, created and
//       serialized by THIS editor) so tools/d7_build.py copies Unity 2019.4's exact Texture2D YAML layout; then quits.
//   BdspD7.Verify (-executeMethod): loads every texture listed in ../work/s34/d7_verify.txt (asset path per line) and writes
//       ../work/s34/d7_verify_result.txt: path, type, format, size, mipmapCount, filter, wrap, and the main object's GUID/fileID;
//       plus, for ../work/s34/d7_verify_materials.txt (material paths), every texture property's resolved object. Then quits.
using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

public static class BdspD7
{
    public static void WriteTemplate()
    {
        try
        {
            Directory.CreateDirectory("Assets/_d7_template");
            var t = new Texture2D(8, 8, TextureFormat.DXT1, true);
            t.name = "d7_template";
            t.filterMode = FilterMode.Bilinear;
            t.wrapMode = TextureWrapMode.Clamp;
            t.anisoLevel = 1;
            AssetDatabase.CreateAsset(t, "Assets/_d7_template/d7_template.asset");
            var u = new Texture2D(4, 4, TextureFormat.RGBA32, false);
            u.name = "d7_template_rgba";
            AssetDatabase.CreateAsset(u, "Assets/_d7_template/d7_template_rgba.asset");
            // BINARY template: the project is ForceText (YAML hex doubles the 13 GiB of texel data - does not fit on E:). The setting
            // is switched to Mixed for this one CreateAsset only; tools/d7_restore_editorsettings re-writes ForceText in the file
            // afterwards (a scripted switch BACK to ForceText would re-serialize every asset of the project).
            EditorSettings.serializationMode = SerializationMode.Mixed;
            var b = new Texture2D(8, 8, TextureFormat.DXT1, true);
            b.name = "d7_template_bin";
            AssetDatabase.CreateAsset(b, "Assets/_d7_template/d7_template_bin.asset");
            AssetDatabase.SaveAssets();
            Debug.Log("BDSP_D7_TEMPLATE_DONE");
        }
        catch (Exception e)
        {
            Debug.LogError("[BdspD7] template: " + e);
        }
        EditorApplication.Exit(0);
    }

    // The automated setup (setup/stages/d7.py): every template in ONE editor session - the four WriteTemplate writes plus the cubemap
    // template - then quits. Switches EditorSettings to Mixed like WriteTemplate; the setup restores ProjectSettings/EditorSettings.asset
    // byte for byte afterwards.
    public static void WriteAllTemplates()
    {
        try
        {
            Directory.CreateDirectory("Assets/_d7_template");
            var t = new Texture2D(8, 8, TextureFormat.DXT1, true);
            t.name = "d7_template";
            t.filterMode = FilterMode.Bilinear;
            t.wrapMode = TextureWrapMode.Clamp;
            t.anisoLevel = 1;
            AssetDatabase.CreateAsset(t, "Assets/_d7_template/d7_template.asset");
            var u = new Texture2D(4, 4, TextureFormat.RGBA32, false);
            u.name = "d7_template_rgba";
            AssetDatabase.CreateAsset(u, "Assets/_d7_template/d7_template_rgba.asset");
            EditorSettings.serializationMode = SerializationMode.Mixed;
            var b = new Texture2D(8, 8, TextureFormat.DXT1, true);
            b.name = "d7_template_bin";
            AssetDatabase.CreateAsset(b, "Assets/_d7_template/d7_template_bin.asset");
            var c = new Cubemap(8, TextureFormat.BC6H, true);
            c.name = "d7_template_cube";
            AssetDatabase.CreateAsset(c, "Assets/_d7_template/d7_template_cube.asset");
            AssetDatabase.SaveAssets();
            Debug.Log("BDSP_D7_TEMPLATES_DONE");
        }
        catch (Exception e)
        {
            Debug.LogError("[BdspD7] templates: " + e);
        }
        EditorApplication.Exit(0);
    }

    // Binary Cubemap template (8x8 BC6H, mips) for tools/d7_cubemaps.py - same Mixed-mode trick as WriteTemplate (the file is restored
    // to ForceText afterwards from work/s34/projectsettings_backup/EditorSettings.asset). Then the same Verify pass, then quits.
    public static void WriteCubemapTemplateAndVerify()
    {
        try
        {
            Directory.CreateDirectory("Assets/_d7_template");
            EditorSettings.serializationMode = SerializationMode.Mixed;
            var c = new Cubemap(8, TextureFormat.BC6H, true);
            c.name = "d7_template_cube";
            AssetDatabase.CreateAsset(c, "Assets/_d7_template/d7_template_cube.asset");
            AssetDatabase.SaveAssets();
            Debug.Log("[BdspD7] cubemap template written");
        }
        catch (Exception e)
        {
            Debug.LogError("[BdspD7] cubemap template: " + e);
        }
        Verify();
    }

    public static void Verify()
    {
        var sb = new StringBuilder();
        // the automated setup passes its work folder in BDSP_SETUP_WORK; without it the workspace layout ../work/s34
        var setupWork = Environment.GetEnvironmentVariable("BDSP_SETUP_WORK");
        var work = string.IsNullOrEmpty(setupWork) ? Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", "work", "s34"))
                                                   : Path.Combine(setupWork, "d7");
        try
        {
            var list = Path.Combine(work, "d7_verify.txt");
            int inspectedTextures = 0;
            if (File.Exists(list))
                foreach (var p in File.ReadAllLines(list))
                {
                    if (p.Trim().Length == 0) continue;
                    var o = AssetDatabase.LoadMainAssetAtPath(p.Trim());
                    var tex = o as Texture2D;
                    string guid; long fid;
                    AssetDatabase.TryGetGUIDAndLocalFileIdentifier(o, out guid, out fid);
                    sb.AppendLine(tex == null ? string.Format("{0}: {1}", p, o == null ? "NULL" : o.GetType().Name)
                        : string.Format("{0}: Texture2D {1} {2}x{3} mips {4} filter {5} wrap {6}/{7} aniso {8} guid {9} fileID {10}", p, tex.format,
                            tex.width, tex.height, tex.mipmapCount, tex.filterMode, tex.wrapModeU, tex.wrapModeV, tex.anisoLevel, guid, fid));
                    // Only the metadata is needed for the report. Release unused textures between batches.
                    if (++inspectedTextures % 1000 == 0)
                    {
                        EditorUtility.UnloadUnusedAssetsImmediate();
                        GC.Collect();
                    }
                }
            var mats = Path.Combine(work, "d7_verify_materials.txt");
            if (File.Exists(mats))
                foreach (var p in File.ReadAllLines(mats))
                {
                    if (p.Trim().Length == 0) continue;
                    var m = AssetDatabase.LoadAssetAtPath<Material>(p.Trim());
                    if (m == null) { sb.AppendLine(p + ": material NULL"); continue; }
                    foreach (var name in m.GetTexturePropertyNames())
                    {
                        var t = m.GetTexture(name);
                        sb.AppendLine(string.Format("{0} {1} = {2}", p, name, t == null ? "null" : AssetDatabase.GetAssetPath(t) + " (" + t.GetType().Name + ")"));
                    }
                }
        }
        catch (Exception e)
        {
            sb.AppendLine("EXCEPTION " + e);
        }
        sb.AppendLine("BDSP_D7_VERIFY_DONE");
        File.WriteAllText(Path.Combine(work, "d7_verify_result.txt"), sb.ToString());
        // the editor re-saves the converted cubemap faces as text (same bytes as the reference project); doing it here instead of
        // inside Exit's shutdown save avoids the editor crashing on the progress-bar repaint of that late re-import
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        Debug.Log("BDSP_D7_VERIFY_DONE");
        EditorApplication.Exit(0);
    }
}
