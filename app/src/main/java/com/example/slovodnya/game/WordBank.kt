package com.example.slovodnya.game

data class WordCategory(
    val title: String,
    val words: List<String>
)

object WordBank {

    // На старте — пара категорий для теста. Список будет расширяться.
    val categories = listOf(
        WordCategory(
            title = "Столицы",
            words = listOf("ПАРИЖ", "ТОКИО", "РИГА", "МИНСК", "ОСЛО", "БЕРН", "КИЕВ")
        ),
        WordCategory(
            title = "Животные",
            words = listOf("ТИГР", "ЗЕБРА", "ВОЛК", "ЛИСА", "СОВА", "РЫСЬ")
        )
    )

    /**
     * Возвращает "слово дня" для категории — детерминированно по номеру дня,
     * чтобы все игроки в один день получали одно и то же слово.
     */
    fun wordOfTheDay(category: WordCategory, dayNumber: Int): String {
        val index = dayNumber % category.words.size
        return category.words[index]
    }
}
