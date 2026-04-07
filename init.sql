CREATE TABLE IF NOT EXISTS jogos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    genero VARCHAR(50),
    preco DECIMAL(10,2),
    estoque INTEGER DEFAULT 0
);

INSERT INTO jogos (nome, genero, preco, estoque) VALUES
('The Legend of Zelda: Tears of the Kingdom', 'Aventura', 299.90, 15),
('Cyberpunk 2077', 'RPG', 199.90, 8),
('Elden Ring', 'Action', 249.90, 12),
('Starfield', 'RPG', 299.90, 5),
('Hogwarts Legacy', 'Aventura', 229.90, 20)
ON CONFLICT DO NOTHING;