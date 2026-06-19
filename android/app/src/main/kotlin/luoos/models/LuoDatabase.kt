package luoos.android.models

import android.content.Context
import androidx.room.*
import kotlinx.coroutines.flow.Flow

// ─── Entity ───────────────────────────────────────────────────────────────────

@Entity(tableName = "luo_memory")
data class LuoMemory(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "content") val content: String,
    @ColumnInfo(name = "tag") val tag: String = "general",
    @ColumnInfo(name = "timestamp") val timestamp: Long = System.currentTimeMillis()
)

@Entity(tableName = "luo_chat_history")
data class LuoChatMessage(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "role") val role: String,       // "user" | "assistant"
    @ColumnInfo(name = "content") val content: String,
    @ColumnInfo(name = "timestamp") val timestamp: Long = System.currentTimeMillis(),
    @ColumnInfo(name = "tool_calls") val toolCalls: String? = null  // JSON if any tools were called
)

// ─── DAOs ─────────────────────────────────────────────────────────────────────

@Dao
interface LuoMemoryDao {
    @Insert
    suspend fun insert(memory: LuoMemory): Long

    @Query("SELECT * FROM luo_memory WHERE content LIKE :query ORDER BY timestamp DESC LIMIT 10")
    suspend fun search(query: String): List<LuoMemory>

    @Query("SELECT * FROM luo_memory ORDER BY timestamp DESC LIMIT 50")
    fun getAllFlow(): Flow<List<LuoMemory>>

    @Delete
    suspend fun delete(memory: LuoMemory)

    @Query("DELETE FROM luo_memory")
    suspend fun deleteAll()
}

@Dao
interface LuoChatDao {
    @Insert
    suspend fun insert(message: LuoChatMessage): Long

    @Query("SELECT * FROM luo_chat_history ORDER BY timestamp DESC LIMIT 100")
    fun getRecentFlow(): Flow<List<LuoChatMessage>>

    @Query("SELECT * FROM luo_chat_history ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecent(limit: Int = 20): List<LuoChatMessage>

    @Query("DELETE FROM luo_chat_history")
    suspend fun clearHistory()

    @Query("SELECT COUNT(*) FROM luo_chat_history")
    suspend fun count(): Int
}

// ─── Database ─────────────────────────────────────────────────────────────────

@Database(
    entities = [LuoMemory::class, LuoChatMessage::class],
    version = 1,
    exportSchema = false
)
abstract class LuoDatabase : RoomDatabase() {
    abstract fun memoryDao(): LuoMemoryDao
    abstract fun chatDao(): LuoChatDao

    companion object {
        @Volatile
        private var INSTANCE: LuoDatabase? = null

        fun getInstance(context: Context): LuoDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    LuoDatabase::class.java,
                    "luo_os.db"
                )
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
