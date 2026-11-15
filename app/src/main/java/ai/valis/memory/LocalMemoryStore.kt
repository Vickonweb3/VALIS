package ai.valis.memory
import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
private val Context.valisStore by preferencesDataStore(name="valis_private_memory")
class LocalMemoryStore(private val context:Context){
 private val key=stringPreferencesKey("user_notes")
 suspend fun readNotes():String=context.valisStore.data.first()[key].orEmpty()
 suspend fun writeNotes(value:String){context.valisStore.edit{it[key]=value}}
 suspend fun clearNotes(){context.valisStore.edit{it.remove(key)}}
}
