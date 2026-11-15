package ai.valis.tools
enum class ToolRisk { SAFE,SENSITIVE,CONSEQUENTIAL }
data class ToolSpec(val id:String,val description:String,val risk:ToolRisk,val requiresConfirmation:Boolean,val permission:String?=null)
class ToolRegistry {
    private val entries=linkedMapOf<String,ToolSpec>()
    fun register(spec:ToolSpec){require(spec.id.isNotBlank());entries[spec.id]=spec}
    fun find(id:String)=entries[id]
    fun all()=entries.values.toList()
    fun allowed(id:String,confirmed:Boolean):Boolean {val s=entries[id]?:return false;return !s.requiresConfirmation||confirmed}
}
