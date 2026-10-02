package com.example.slovodnya.game

/**
 * Сравнивает введённое слово с загаданным и возвращает состояние каждой буквы.
 * Корректно обрабатывает повторяющиеся буквы (двухпроходный алгоритм):
 * сначала отмечаются точные совпадения, затем — буквы "не на своём месте"
 * среди ещё не использованных позиций загаданного слова.
 */
object GuessEvaluator {

    fun evaluate(guess: String, target: String): List<LetterState> {
        require(guess.length == target.length) { "Длина слова не совпадает с загаданным" }

        val result = MutableList(guess.length) { LetterState.ABSENT }
        val targetChars = target.toCharArray()
        val used = BooleanArray(target.length)

        // 1 проход — точные совпадения (буква и позиция верны)
        for (i in guess.indices) {
            if (guess[i] == targetChars[i]) {
                result[i] = LetterState.CORRECT
                used[i] = true
            }
        }

        // 2 проход — буква есть в слове, но на другом месте
        for (i in guess.indices) {
            if (result[i] == LetterState.CORRECT) continue

            val foundIndex = targetChars.withIndex().firstOrNull { (j, c) ->
                c == guess[i] && !used[j]
            }?.index

            if (foundIndex != null) {
                result[i] = LetterState.PRESENT
                used[foundIndex] = true
            }
        }

        return result
    }
}
