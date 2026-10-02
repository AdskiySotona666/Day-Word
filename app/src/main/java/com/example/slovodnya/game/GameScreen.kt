package com.example.slovodnya.game

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun GameScreen(viewModel: GameViewModel) {
    val state by viewModel.state.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(text = "Слово Дня", fontSize = 24.sp, fontWeight = FontWeight.Bold)
        Text(text = "Категория: ${state.categoryTitle}")

        Spacer(modifier = Modifier.height(16.dp))

        GuessBoard(state = state)

        Spacer(modifier = Modifier.height(16.dp))

        when (state.status) {
            GameStatus.WON -> Text("Поздравляем, угадано! \uD83C\uDF89")
            GameStatus.LOST -> Text("Не угадано. Слово было: ${state.targetWord}")
            GameStatus.PLAYING -> {}
        }

        Spacer(modifier = Modifier.height(16.dp))

        SimpleKeyboard(
            onLetter = viewModel::onLetterInput,
            onDelete = viewModel::onDelete,
            onSubmit = viewModel::onSubmit
        )
    }
}

@Composable
private fun GuessBoard(state: GameState) {
    Column {
        state.submittedGuesses.forEach { row ->
            GuessRowView(letters = row.letters, states = row.states)
        }

        if (state.status == GameStatus.PLAYING) {
            val currentLetters = state.currentInput.toList()
            val paddedLetters = currentLetters + List(state.wordLength - currentLetters.size) { ' ' }
            val currentStates = List(state.wordLength) { LetterState.TYPED }
            GuessRowView(letters = paddedLetters, states = currentStates)
        }

        val typedRow = if (state.status == GameStatus.PLAYING) 1 else 0
        val remainingRows = state.maxAttempts - state.submittedGuesses.size - typedRow
        repeat(remainingRows.coerceAtLeast(0)) {
            GuessRowView(
                letters = List(state.wordLength) { ' ' },
                states = List(state.wordLength) { LetterState.EMPTY }
            )
        }
    }
}

@Composable
private fun GuessRowView(letters: List<Char>, states: List<LetterState>) {
    Row {
        letters.forEachIndexed { index, letter ->
            LetterTile(letter = letter, state = states[index])
        }
    }
}

@Composable
private fun LetterTile(letter: Char, state: LetterState) {
    val backgroundColor = when (state) {
        LetterState.CORRECT -> Color(0xFF6AAA64)
        LetterState.PRESENT -> Color(0xFFC9B458)
        LetterState.ABSENT -> Color(0xFF787C7E)
        LetterState.TYPED -> Color.White
        LetterState.EMPTY -> Color.White
    }
    val borderColor = if (state == LetterState.EMPTY || state == LetterState.TYPED) {
        Color(0xFFD3D6DA)
    } else {
        backgroundColor
    }
    val textColor = if (state == LetterState.EMPTY || state == LetterState.TYPED) {
        Color.Black
    } else {
        Color.White
    }

    Box(
        modifier = Modifier
            .padding(2.dp)
            .size(48.dp)
            .background(backgroundColor)
            .border(width = 2.dp, color = borderColor),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = if (letter == ' ') "" else letter.toString(),
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = textColor
        )
    }
}

@Composable
private fun SimpleKeyboard(
    onLetter: (Char) -> Unit,
    onDelete: () -> Unit,
    onSubmit: () -> Unit
) {
    val rows = listOf(
        "ЙЦУКЕНГШЩЗХ",
        "ФЫВАПРОЛДЖЭ",
        "ЯЧСМИТЬБЮ"
    )

    Column(modifier = Modifier.fillMaxWidth()) {
        rows.forEach { row ->
            Row(modifier = Modifier.fillMaxWidth()) {
                row.forEach { char ->
                    KeyButton(
                        text = char.toString(),
                        modifier = Modifier.weight(1f),
                        onClick = { onLetter(char) }
                    )
                }
            }
        }
        Row(modifier = Modifier.fillMaxWidth()) {
            KeyButton(text = "⌫", modifier = Modifier.weight(2f), onClick = onDelete)
            KeyButton(text = "Ввод", modifier = Modifier.weight(3f), onClick = onSubmit)
        }
    }
}

@Composable
private fun KeyButton(text: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier = modifier
            .padding(2.dp)
            .height(42.dp)
            .background(Color(0xFFD3D6DA), shape = RoundedCornerShape(4.dp))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            color = Color.Black
        )
    }
}