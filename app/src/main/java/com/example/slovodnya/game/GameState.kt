package com.example.slovodnya.game

data class GuessRow(
    val letters: List<Char>,
    val states: List<LetterState>
)

enum class GameStatus { PLAYING, WON, LOST }

data class GameState(
    val targetWord: String = "",
    val wordLength: Int = 5,
    val maxAttempts: Int = 6,
    val submittedGuesses: List<GuessRow> = emptyList(),
    val currentInput: String = "",
    val status: GameStatus = GameStatus.PLAYING,
    val categoryTitle: String = ""
)
