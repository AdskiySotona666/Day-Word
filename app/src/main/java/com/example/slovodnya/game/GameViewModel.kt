package com.example.slovodnya.game

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.Calendar

class GameViewModel : ViewModel() {

    private val category = WordBank.categories.first()
    private val dayNumber = Calendar.getInstance().get(Calendar.DAY_OF_YEAR)
    private val targetWord = WordBank.wordOfTheDay(category, dayNumber)

    private val _state = MutableStateFlow(
        GameState(
            targetWord = targetWord,
            wordLength = targetWord.length,
            categoryTitle = category.title
        )
    )
    val state: StateFlow<GameState> = _state.asStateFlow()

    fun onLetterInput(letter: Char) {
        val current = _state.value
        if (current.status != GameStatus.PLAYING) return
        if (current.currentInput.length >= current.wordLength) return

        _state.value = current.copy(currentInput = current.currentInput + letter.uppercaseChar())
    }

    fun onDelete() {
        val current = _state.value
        if (current.status != GameStatus.PLAYING) return
        if (current.currentInput.isEmpty()) return

        _state.value = current.copy(currentInput = current.currentInput.dropLast(1))
    }

    fun onSubmit() {
        val current = _state.value
        if (current.status != GameStatus.PLAYING) return
        if (current.currentInput.length != current.wordLength) return

        val evaluation = GuessEvaluator.evaluate(current.currentInput, current.targetWord)
        val newRow = GuessRow(letters = current.currentInput.toList(), states = evaluation)
        val newGuesses = current.submittedGuesses + newRow

        val newStatus = when {
            current.currentInput == current.targetWord -> GameStatus.WON
            newGuesses.size >= current.maxAttempts -> GameStatus.LOST
            else -> GameStatus.PLAYING
        }

        _state.value = current.copy(
            submittedGuesses = newGuesses,
            currentInput = "",
            status = newStatus
        )
    }
}
