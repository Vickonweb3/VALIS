package ai.valis.character.pose

import org.json.JSONObject
import org.junit.Assume.assumeTrue
import org.junit.Assert.*
import org.junit.Test
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Checks the shipped model against the shipped animation pack, with no device and no GPU.
 * Skipped when the model is absent or is still a Git LFS pointer (checkout without LFS).
 */
class RealAssetTest {
    private val dir = File("src/main/assets/valis")
    private val glbFile = File(dir, "VALIS_rigged.glb")

    private fun gltfJson(): JSONObject {
        assumeTrue("model not present or not fetched from LFS", glbFile.isFile && glbFile.length() > 100_000)
        val head = ByteBuffer.wrap(glbFile.inputStream().use { it.readNBytes(20) }).order(ByteOrder.LITTLE_ENDIAN)
        assertEquals("glTF magic", 0x46546C67, head.getInt(0))
        val jsonLen = head.getInt(12)
        val bytes = glbFile.inputStream().use { it.skipNBytes(20); it.readNBytes(jsonLen) }
        return JSONObject(String(bytes, Charsets.UTF_8))
    }

    private fun pack() = AnimationPack.parse(File(dir, "valis_anim.v1.json").readText(), File(dir, "valis_anim.v1.bin").readBytes())

    @Test fun shippedPackBindsToShippedModel() {
        val g = gltfJson()
        val nodes = g.getJSONArray("nodes")
        val byName = HashMap<String, Int>()
        for (i in 0 until nodes.length()) nodes.getJSONObject(i).optString("name").takeIf { it.isNotEmpty() }?.let { byName[it] = i }
        val meshes = g.getJSONArray("meshes")
        fun morphNames(node: Int): List<String> {
            val mesh = nodes.getJSONObject(node).optInt("mesh", -1)
            if (mesh < 0) return emptyList()
            val t = meshes.getJSONObject(mesh).optJSONObject("extras")?.optJSONArray("targetNames") ?: return emptyList()
            return List(t.length()) { t.getString(it) }
        }
        val rig = RigBinder.bind(pack(), { byName[it] }, ::morphNames)
        assertEquals(27, rig.jointEntities.size)
        assertEquals(setOf("VALIS_body", "VALIS_mouth"), rig.meshEntities.keys)
    }

    @Test fun everyClipSamplesWithoutErrorAndStaysFinite() {
        val pack = pack()
        val n = pack.joints.size
        val rest = RestPose(FloatArray(n * 4) { if (it % 4 == 3) 1f else 0f }, FloatArray(n * 3), FloatArray(n * 3) { 1f })
        val counts = pack.morphs.mapValues { it.value.size }
        for (clip in pack.clips) {
            val rt = PoseRuntime(pack, rest, counts)
            assertTrue(clip.name, rt.play(Layer.BASE, clip.name, loop = false, fadeSeconds = 0f))
            var t = 0f
            while (t < clip.duration + 0.2f) {
                val p = rt.update(1f / 30); t += 1f / 30
                for (v in p.rotation) assertTrue("${clip.name} rotation", v.isFinite())
                for (a in p.morphs.values) for (v in a) assertTrue("${clip.name} morph $v", v.isFinite() && v in 0f..1f)
            }
        }
    }
}
