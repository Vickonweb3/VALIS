package ai.valis.ai
/** Provider contract; configure the selected inference endpoint and credentials outside source control. */
interface ModelProvider { suspend fun respond(input:ModelInput):ModelOutput }
data class ModelInput(val text:String?=null,val imageBytes:ByteArray?=null,val conversationId:String?=null)
data class ModelOutput(val text:String,val emotion:String?=null,val requestedTool:String?=null)
