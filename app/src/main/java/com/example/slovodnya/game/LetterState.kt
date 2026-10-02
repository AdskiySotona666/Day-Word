package com.example.slovodnya.game

enum class LetterState {
    EMPTY,      // буква ещё не введена (пустая клетка)
    TYPED,      // буква введена, но попытка ещё не проверена
    ABSENT,     // буквы нет в загаданном слове
    PRESENT,    // буква есть в слове, но стоит не на своём месте
    CORRECT     // буква стоит на правильном месте
}
