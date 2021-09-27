from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats_male = (
        '{{first_name_male}} {{last_name}} {{last_name}}',
        '{{first_name_male}} {{last_name}} {{last_name}}',
        '{{first_name_male}} {{last_name}} {{last_name}}',
        '{{first_name_male}} {{last_name}} {{last_name}}',
        '{{first_name_male}} {{last_name}} {{last_name}}',
        '{{first_name_male}} {{last_name}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{prefix}} {{last_name}}',
        '{{first_name_male}} {{last_name}}-{{last_name}}',
        '{{first_name_male}} {{first_name_male}} {{last_name}} {{last_name}}',
    )

    formats_female = (
        '{{first_name_female}} {{last_name}} {{last_name}}',
        '{{first_name_female}} {{last_name}} {{last_name}}',
        '{{first_name_female}} {{last_name}} {{last_name}}',
        '{{first_name_female}} {{last_name}} {{last_name}}',
        '{{first_name_female}} {{last_name}} {{last_name}}',
        '{{first_name_female}} {{last_name}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{prefix}} {{last_name}}',
        '{{first_name_female}} {{last_name}}-{{last_name}}',
        '{{first_name_female}} {{first_name_female}} {{last_name}} {{last_name}}',
    )

    formats = formats_male + formats_female

    # 477 male first names, alphabetically.
    # Source: Álvaro Mondéjar Rubio <mondejar1994@gmail.com>
    first_names_male = (
        'Aarón', 'Abel', 'Abilio', 'Abraham', 'Adalberto',
        'Adelardo', 'Adolfo', 'Adrián', 'Adán', 'Agapito', 'Agustín',
        'Aitor', 'Albano', 'Albert', 'Alberto', 'Albino', 'Alcides',
        'Ale', 'Alejandro', 'Alejo', 'Alex', 'Alfonso', 'Alfredo',
        'Alonso', 'Amado', 'Amador', 'Amancio', 'Amando', 'Amaro',
        'Ambrosio', 'Amor', 'Américo', 'Amílcar', 'Anacleto', 'Anastasio',
        'Andrés', 'Andrés Felipe', 'Angelino', 'Anselmo', 'Antonio',
        'Aníbal', 'Apolinar', 'Ariel', 'Aristides', 'Armando',
        'Arsenio', 'Artemio', 'Arturo', 'Asdrubal', 'Atilio', 'Augusto',
        'Aureliano', 'Aurelio', 'Baldomero', 'Balduino', 'Baltasar',
        'Bartolomé', 'Basilio', 'Baudelio', 'Bautista', 'Benigno',
        'Benito', 'Benjamín', 'Bernabé', 'Bernardino', 'Bernardo',
        'Berto', 'Blas', 'Bonifacio', 'Borja', 'Bruno', 'Buenaventura',
        'Calisto', 'Calixto', 'Camilo', 'Candelario', 'Carlito',
        'Carlos', 'Carmelo', 'Casemiro', 'Cayetano', 'Cebrián',
        'Cecilio', 'Ceferino', 'Celestino', 'Celso', 'Cesar', 'Che',
        'Chema', 'Chucho', 'Chus', 'Chuy', 'Cipriano', 'Ciriaco',
        'Cirino', 'Ciro', 'Ciríaco', 'Claudio', 'Clemente', 'Cleto',
        'Clímaco', 'Conrado', 'Cornelio', 'Cosme', 'Cristian',
        'Cristian', 'Cristóbal', 'Cruz', 'Curro', 'Custodio', 'Cándido',
        'César', 'Damián', 'Dan', 'Dani', 'Daniel', 'Danilo', 'Darío',
        'David', 'Demetrio', 'Desiderio', 'Diego', 'Dimas', 'Dionisio',
        'Domingo', 'Donato', 'Duilio', 'Edelmiro', 'Edgardo', 'Edmundo',
        'Edu', 'Eduardo', 'Efraín', 'Eladio', 'Eleuterio', 'Eligio',
        'Eliseo', 'Eloy', 'Elpidio', 'Elías', 'Emigdio', 'Emiliano',
        'Emilio', 'Enrique', 'Epifanio', 'Erasmo', 'Eric', 'Ernesto',
        'Espiridión', 'Esteban', 'Eugenio', 'Eusebio', 'Eustaquio',
        'Eutimio', 'Eutropio', 'Evaristo', 'Ezequiel', 'Fabio', 'Fabián',
        'Fabricio', 'Faustino', 'Fausto', 'Federico', 'Feliciano',
        'Felipe', 'Felix', 'Fermín', 'Fernando', 'Fidel', 'Fito',
        'Flavio', 'Florencio', 'Florentino', 'Fortunato', 'Francisco',
        'Francisco Javier', 'Francisco Jose', 'Fulgencio', 'Félix', 'Gabino',
        'Gabriel', 'Galo', 'Gaspar', 'Gastón', 'Geraldo', 'Gerardo',
        'Germán', 'Gervasio', 'Gerónimo', 'Gil', 'Gilberto', 'Glauco',
        'Godofredo', 'Gonzalo', 'Goyo', 'Graciano', 'Gregorio',
        'Guadalupe', 'Guillermo', 'Guiomar', 'Gustavo', 'Haroldo',
        'Hector', 'Heliodoro', 'Heraclio', 'Herberto', 'Heriberto',
        'Hermenegildo', 'Herminio', 'Hernando', 'Hernán', 'Hilario',
        'Hipólito', 'Horacio', 'Hugo', 'Humberto', 'Héctor', 'Ibán',
        'Ignacio', 'Iker', 'Ildefonso', 'Inocencio', 'Isaac', 'Isaías',
        'Isidoro', 'Isidro', 'Ismael', 'Iván', 'Jacinto', 'Jacobo',
        'Jafet', 'Jaime', 'Javi', 'Javier', 'Jenaro', 'Jeremías',
        'Jerónimo', 'Jesús', 'Joan', 'Joaquín', 'Joel', 'Jonatan', 'Jordi',
        'Jordán', 'Jorge', 'Jose', 'Jose Angel', 'Jose Antonio',
        'Jose Carlos', 'Jose Francisco', 'Jose Ignacio', 'Jose Luis',
        'Jose Manuel', 'Jose Miguel', 'Jose Ramón', 'Josep', 'Josué', 'José',
        'José Antonio', 'José Luis', 'José Manuel', 'José Mari',
        'José María', 'José Ángel', 'Juan', 'Juan Antonio',
        'Juan Bautista', 'Juan Carlos', 'Juan Francisco', 'Juan José',
        'Juan Luis', 'Juan Manuel', 'Juan Pablo', 'Juanito', 'Julio',
        'Julio César', 'Julián', 'Kike', 'Lalo', 'Leandro', 'Leocadio',
        'Leonardo', 'Leoncio', 'Leonel', 'Leopoldo', 'León', 'Lino',
        'Lisandro', 'Lope', 'Lorenzo', 'Loreto', 'Lucas', 'Lucho',
        'Luciano', 'Lucio', 'Luis', 'Luis Miguel', 'Luis Ángel', 'Lupe',
        'Luís', 'Lázaro', 'Macario', 'Manolo', 'Manu', 'Manuel',
        'Marc', 'Marcelino', 'Marcelo', 'Marcial', 'Marciano',
        'Marcio', 'Marco', 'Marcos', 'Mariano', 'Marino', 'Mario',
        'Martin', 'Martín', 'María', 'Mateo', 'Matías', 'Mauricio',
        'Maxi', 'Maximiano', 'Maximiliano', 'Maximino', 'Melchor',
        'Miguel', 'Miguel Ángel', 'Modesto', 'Mohamed', 'Moisés',
        'Moreno', 'Máximo', 'Nacho', 'Nacio', 'Nando', 'Narciso',
        'Natalio', 'Natanael', 'Nazaret', 'Nazario', 'Nicanor', 'Nico',
        'Nicodemo', 'Nicolás', 'Nilo', 'Norberto', 'Noé', 'Néstor',
        'Octavio', 'Olegario', 'Omar', 'Onofre', 'Osvaldo', 'Ovidio',
        'Pablo', 'Paco', 'Pancho', 'Pascual', 'Pastor', 'Patricio',
        'Paulino', 'Pedro', 'Pelayo', 'Pepe', 'Pepito', 'Plinio',
        'Plácido', 'Poncio', 'Porfirio', 'Primitivo', 'Prudencio',
        'Pánfilo', 'Pío', 'Quique', 'Quirino', 'Rafa', 'Rafael',
        'Raimundo', 'Ramiro', 'Ramón', 'Raúl', 'Reinaldo', 'Remigio',
        'Renato', 'René', 'Reyes', 'Reynaldo', 'Ricardo', 'Rico',
        'Roberto', 'Rodolfo', 'Rodrigo', 'Rogelio', 'Rolando', 'Roldán',
        'Román', 'Roque', 'Rosario', 'Rosendo', 'Ruben', 'Rubén',
        'Rufino', 'Ruperto', 'Ruy', 'Régulo', 'Rómulo', 'Sabas',
        'Salomón', 'Salvador', 'Samu', 'Samuel', 'Sancho', 'Sandalio',
        'Santiago', 'Santos', 'Saturnino', 'Sebastian', 'Sebastián',
        'Segismundo', 'Sergio', 'Seve', 'Severiano', 'Severino', 'Severo',
        'Sigfrido', 'Silvestre', 'Silvio', 'Simón', 'Sosimo', 'Tadeo',
        'Telmo', 'Teo', 'Teobaldo', 'Teodoro', 'Teodosio', 'Teófilo',
        'Tiburcio', 'Timoteo', 'Tito', 'Tomás', 'Toni', 'Toribio', 'Toño',
        'Trinidad', 'Tristán', 'Ulises', 'Urbano', 'Valentín', 'Valerio',
        'Valero', 'Vasco', 'Venceslás', 'Vicente', 'Victor',
        'Victor Manuel', 'Victoriano', 'Victorino', 'Vidal', 'Vinicio',
        'Virgilio', 'Vito', 'Víctor', 'Wilfredo', 'Wálter', 'Xavier',
        'Yago', 'Zacarías', 'Álvaro', 'Ángel', 'Édgar', 'Íñigo',
        'Óscar',
    )

    # 477 female first names, alphabetically.
    # Source: Álvaro Mondéjar Rubio <mondejar1994@gmail.com>
    first_names_female = (
        'Abigaíl', 'Abril', 'Adela', 'Adelaida', 'Adelia',
        'Adelina', 'Adora', 'Adoración', 'Adriana', 'Agustina', 'Ainara',
        'Ainoa', 'Aitana', 'Alba', 'Albina', 'Ale', 'Alejandra',
        'Alexandra', 'Alicia', 'Alma', 'Almudena', 'Alondra', 'Amada',
        'Amalia', 'Amanda', 'Amarilis', 'Amaya', 'Amelia', 'Amor',
        'Amparo', 'América', 'Ana', 'Ana Belén', 'Ana Sofía', 'Anabel',
        'Anastasia', 'Andrea', 'Angelina', 'Angelita', 'Angélica', 'Ani',
        'Anita', 'Anna', 'Anselma', 'Antonia', 'Anunciación',
        'Apolonia', 'Araceli', 'Arcelia', 'Ariadna', 'Ariel', 'Armida',
        'Aroa', 'Aránzazu', 'Ascensión', 'Asunción', 'Aura',
        'Aurelia', 'Aurora', 'Azahar', 'Azahara', 'Azeneth', 'Azucena',
        'Beatriz', 'Begoña', 'Belen', 'Belén', 'Benigna', 'Benita',
        'Bernarda', 'Bernardita', 'Berta', 'Bibiana', 'Bienvenida',
        'Blanca', 'Brunilda', 'Brígida', 'Bárbara', 'Calista',
        'Calixta', 'Camila', 'Candela', 'Candelaria', 'Candelas',
        'Caridad', 'Carina', 'Carla', 'Carlota', 'Carmela', 'Carmelita',
        'Carmen', 'Carmina', 'Carolina', 'Casandra', 'Catalina',
        'Cayetana', 'Cecilia', 'Celestina', 'Celia', 'Charo', 'Chelo',
        'Chita', 'Chus', 'Cintia', 'Clara', 'Clarisa', 'Claudia',
        'Clementina', 'Cloe', 'Clotilde', 'Concepción', 'Concha',
        'Constanza', 'Consuela', 'Consuelo', 'Coral', 'Corona',
        'Crescencia', 'Cristina', 'Cruz', 'Custodia', 'Cándida', 'Dafne',
        'Dalila', 'Daniela', 'Delfina', 'Delia', 'Diana', 'Dionisia',
        'Dolores', 'Dominga', 'Domitila', 'Dora', 'Dorita', 'Dorotea',
        'Dulce', 'Débora', 'Edelmira', 'Elba', 'Elena', 'Eli', 'Eliana',
        'Eligia', 'Elisa', 'Elisabet', 'Elodia', 'Eloísa', 'Elvira',
        'Ema', 'Emelina', 'Emilia', 'Emiliana', 'Emma', 'Emperatriz',
        'Encarna', 'Encarnacion', 'Encarnación', 'Encarnita',
        'Esmeralda', 'Esperanza', 'Estefanía', 'Estela', 'Ester', 'Esther',
        'Estrella', 'Etelvina', 'Eufemia', 'Eugenia', 'Eulalia',
        'Eusebia', 'Eva', 'Eva María', 'Evangelina', 'Evelia', 'Evita',
        'Fabiana', 'Fabiola', 'Fanny', 'Febe', 'Felicia', 'Feliciana',
        'Felicidad', 'Felipa', 'Felisa', 'Fernanda', 'Fidela', 'Filomena',
        'Flavia', 'Flor', 'Flora', 'Florencia', 'Florentina', 'Florina',
        'Florinda', 'Fortunata', 'Francisca', 'Fátima', 'Gabriela',
        'Gala', 'Gema', 'Genoveva', 'Georgina', 'Gertrudis', 'Gisela',
        'Gloria', 'Gracia', 'Graciana', 'Graciela', 'Griselda',
        'Guadalupe', 'Guiomar', 'Haydée', 'Herminia', 'Hilda', 'Hortensia',
        'Ignacia', 'Ileana', 'Imelda', 'Inmaculada', 'Inés', 'Irene',
        'Iris', 'Irma', 'Isa', 'Isabel', 'Isabela', 'Isaura',
        'Isidora', 'Itziar', 'Jacinta', 'Javiera', 'Jennifer', 'Jenny',
        'Jessica', 'Jesusa', 'Jimena', 'Joaquina', 'Jordana', 'Josefa',
        'Josefina', 'José', 'Jovita', 'Juana', 'Juanita', 'Judith',
        'Julia', 'Juliana', 'Julie', 'Julieta', 'Lara', 'Laura',
        'Leandra', 'Leire', 'Leocadia', 'Leonor', 'Leticia', 'Leyre',
        'Lidia', 'Ligia', 'Lilia', 'Liliana', 'Lina', 'Loida', 'Lola',
        'Lorena', 'Lorenza', 'Loreto', 'Lourdes', 'Luciana', 'Lucila',
        'Lucía', 'Luisa', 'Luisina', 'Luna', 'Lupe', 'Lupita', 'Luz',
        'Macarena', 'Macaria', 'Magdalena', 'Maite', 'Malena', 'Mamen',
        'Manola', 'Manu', 'Manuela', 'Manuelita', 'Mar', 'Marcela',
        'Marcia', 'Margarita', 'Mariana', 'Marianela', 'Maribel',
        'Maricela', 'Maricruz', 'Marina', 'Marisa', 'Marisela', 'Marisol',
        'Maristela', 'Marita', 'Marta', 'Martina', 'Martirio', 'María',
        'María Belén', 'María Carmen', 'María Cristina',
        'María Del Carmen', 'María Dolores', 'María Fernanda', 'María Jesús',
        'María José', 'María Luisa', 'María Manuela', 'María Pilar',
        'María Teresa', 'María Ángeles', 'Matilde', 'Maura', 'Maxi', 'Mayte',
        'Melania', 'Melisa', 'Mercedes', 'Merche', 'Micaela', 'Miguela',
        'Milagros', 'Mireia', 'Miriam', 'Mirta', 'Modesta', 'Montserrat',
        'Morena', 'Máxima', 'Mónica', 'Nadia', 'Narcisa', 'Natalia',
        'Natividad', 'Nayara', 'Nazaret', 'Nerea', 'Nereida', 'Nicolasa',
        'Nidia', 'Nieves', 'Nilda', 'Noa', 'Noelia', 'Noemí', 'Nuria',
        'Nydia', 'Nélida', 'Obdulia', 'Octavia', 'Odalis', 'Odalys',
        'Ofelia', 'Olalla', 'Olga', 'Olimpia', 'Olivia', 'Oriana',
        'Otilia', 'Paca', 'Pacífica', 'Palmira', 'Paloma', 'Paola',
        'Pascuala', 'Pastora', 'Patricia', 'Paula', 'Paulina', 'Paz',
        'Pepita', 'Perla', 'Perlita', 'Petrona', 'Piedad', 'Pilar',
        'Pili', 'Primitiva', 'Priscila', 'Prudencia', 'Purificación',
        'Pía', 'Rafaela', 'Ramona', 'Raquel', 'Rebeca', 'Regina',
        'Reina', 'Remedios', 'Renata', 'Reyes', 'Reyna', 'Ricarda',
        'Rita', 'Roberta', 'Rocío', 'Rosa', 'Rosa María', 'Rosalina',
        'Rosalinda', 'Rosalva', 'Rosalía', 'Rosario', 'Rosaura', 'Rosenda',
        'Roxana', 'Rufina', 'Ruperta', 'Ruth', 'Sabina', 'Salomé',
        'Salud', 'Samanta', 'Sandra', 'Sara', 'Sarita', 'Saturnina',
        'Selena', 'Serafina', 'Silvia', 'Socorro', 'Sofía', 'Sol',
        'Soledad', 'Sonia', 'Soraya', 'Susana', 'Susanita', 'Tamara',
        'Tania', 'Tatiana', 'Tecla', 'Teodora', 'Tere', 'Teresa',
        'Teresita', 'Teófila', 'Tomasa', 'Trini', 'Trinidad', 'Valentina',
        'Valeria', 'Vanesa', 'Vera', 'Verónica', 'Vicenta', 'Victoria',
        'Vilma', 'Violeta', 'Virginia', 'Visitación', 'Viviana',
        'Ximena', 'Xiomara', 'Yaiza', 'Yolanda', 'Yésica', 'Yéssica',
        'Zaida', 'Zaira', 'Zoraida', 'África', 'Ágata', 'Águeda',
        'Ámbar', 'Ángela', 'Ángeles', 'Áurea', 'Íngrid', 'Úrsula',
    )

    first_names = first_names_male + first_names_female

    last_names = (
        'Abad', 'Abascal', 'Abella', 'Abellán', 'Abril', 'Acedo', 'Acero',
        'Acevedo', 'Acosta', 'Acuña', 'Adadia', 'Adán', 'Aguado', 'Agudo',
        'Aguilar', 'Aguilera', 'Aguiló', 'Aguirre', 'Agullo', 'Agustí', 'Agustín',
        'Alarcón', 'Alba', 'Alberdi', 'Albero', 'Alberola', 'Alberto', 'Alcalde',
        'Alcalá', 'Alcaraz', 'Alcolea', 'Alcántara', 'Alcázar', 'Alegre', 'Alegria',
        'Alemany', 'Alemán', 'Alfaro', 'Alfonso', 'Aliaga', 'Aller', 'Almagro',
        'Almansa', 'Almazán', 'Almeida', 'Alonso', 'Alsina', 'Alvarado', 'Alvarez',
        'Amador', 'Amat', 'Amaya', 'Amigó', 'Amo', 'Amor', 'Amores',
        'Amorós', 'Anaya', 'Andrade', 'Andres', 'Andreu', 'Andrés', 'Anglada',
        'Anguita', 'Angulo', 'Antón', 'Antúnez', 'Aparicio', 'Aragonés', 'Aragón',
        'Aramburu', 'Arana', 'Aranda', 'Araujo', 'Arce', 'Arco', 'Arcos',
        'Arellano', 'Arenas', 'Arias', 'Ariza', 'Ariño', 'Arjona', 'Armas',
        'Armengol', 'Arnaiz', 'Arnal', 'Arnau', 'Aroca', 'Arranz', 'Arregui',
        'Arribas', 'Arrieta', 'Arroyo', 'Arteaga', 'Artigas', 'Arévalo', 'Asenjo',
        'Asensio', 'Atienza', 'Avilés', 'Ayala', 'Ayllón', 'Ayuso', 'Azcona',
        'Aznar', 'Azorin', 'Badía', 'Baena', 'Baeza', 'Balaguer', 'Ballester',
        'Ballesteros', 'Baquero', 'Barba', 'Barbero', 'Barberá', 'Barceló', 'Barco',
        'Barragán', 'Barral', 'Barranco', 'Barreda', 'Barrena', 'Barrera', 'Barriga',
        'Barrio', 'Barrios', 'Barros', 'Barroso', 'Bartolomé', 'Baró', 'Barón',
        'Bas', 'Bastida', 'Batalla', 'Batlle', 'Bautista', 'Bauzà', 'Bayo',
        'Bayona', 'Bayón', 'Baños', 'Becerra', 'Bejarano', 'Belda', 'Bellido',
        'Bello', 'Belmonte', 'Beltran', 'Beltrán', 'Benavent', 'Benavente', 'Benavides',
        'Benet', 'Benitez', 'Benito', 'Benítez', 'Berenguer', 'Bermejo', 'Bermudez',
        'Bermúdez', 'Bernad', 'Bernal', 'Bernat', 'Berrocal', 'Bertrán', 'Bilbao',
        'Blanca', 'Blanch', 'Blanco', 'Blanes', 'Blasco', 'Blazquez', 'Blázquez',
        'Boada', 'Boix', 'Bolaños', 'Bonet', 'Bonilla', 'Borja', 'Borrego',
        'Borrell', 'Borrás', 'Bosch', 'Botella', 'Bou', 'Bravo', 'Briones',
        'Bru', 'Buendía', 'Bueno', 'Burgos', 'Busquets', 'Bustamante', 'Bustos',
        'Báez', 'Bárcena', 'Caballero', 'Cabanillas', 'Cabañas', 'Cabello', 'Cabeza',
        'Cabezas', 'Cabo', 'Cabrera', 'Cabrero', 'Cadenas', 'Cal', 'Calatayud',
        'Calderon', 'Calderón', 'Calleja', 'Calvet', 'Calvo', 'Calzada', 'Camacho',
        'Camino', 'Campillo', 'Campo', 'Campos', 'Campoy', 'Camps', 'Canales',
        'Canals', 'Canet', 'Cano', 'Cantero', 'Cantón', 'Caparrós', 'Capdevila',
        'Carbajo', 'Carballo', 'Carbonell', 'Carbó', 'Cardona', 'Carlos', 'Carmona',
        'Carnero', 'Caro', 'Carpio', 'Carranza', 'Carrasco', 'Carrera', 'Carreras',
        'Carretero', 'Carreño', 'Carrillo', 'Carrión', 'Carro', 'Carvajal', 'Casado',
        'Casal', 'Casals', 'Casanova', 'Casanovas', 'Casares', 'Casas', 'Cases',
        'Castañeda', 'Castejón', 'Castell', 'Castellanos', 'Castells', 'Castelló', 'Castilla',
        'Castillo', 'Castrillo', 'Castro', 'Catalá', 'Catalán', 'Cazorla', 'Cañas',
        'Cañellas', 'Cañete', 'Cañizares', 'Cepeda', 'Cerdá', 'Cerdán', 'Cerezo',
        'Cerro', 'Cervantes', 'Cervera', 'Chacón', 'Chamorro', 'Chaparro', 'Chaves',
        'Checa', 'Chico', 'Cid', 'Cifuentes', 'Cisneros', 'Clavero', 'Clemente',
        'Cobo', 'Cobos', 'Coca', 'Codina', 'Coello', 'Coll', 'Collado',
        'Colom', 'Coloma', 'Colomer', 'Comas', 'Company', 'Conde', 'Conesa',
        'Contreras', 'Corbacho', 'Cordero', 'Cornejo', 'Corominas', 'Coronado', 'Corral',
        'Correa', 'Cortes', 'Cortina', 'Cortés', 'Costa', 'Crespi', 'Crespo',
        'Criado', 'Cruz', 'Cuadrado', 'Cuenca', 'Cuervo', 'Cuesta', 'Cueto',
        'Cuevas', 'Cuéllar', 'Cáceres', 'Cámara', 'Cánovas', 'Cárdenas', 'Céspedes',
        'Córdoba', 'Cózar', 'Dalmau', 'Daza', 'Delgado', 'Diaz', 'Diego',
        'Diez', 'Diéguez', 'Domingo', 'Dominguez', 'Doménech', 'Domínguez', 'Donaire',
        'Donoso', 'Duarte', 'Dueñas', 'Duque', 'Duran', 'Durán', 'Dávila',
        'Díaz', 'Díez', 'Echevarría', 'Echeverría', 'Egea', 'Elorza', 'Elías',
        'Enríquez', 'Escalona', 'Escamilla', 'Escobar', 'Escolano', 'Escribano', 'Escrivá',
        'Escudero', 'Espada', 'Esparza', 'España', 'Español', 'Espejo', 'Espinosa',
        'Esteban', 'Esteve', 'Estevez', 'Estrada', 'Estévez', 'Exposito', 'Expósito',
        'Fabra', 'Fabregat', 'Fajardo', 'Falcó', 'Falcón', 'Farré', 'Feijoo',
        'Feliu', 'Fernandez', 'Fernández', 'Ferrando', 'Ferrer', 'Ferrera', 'Ferreras',
        'Ferrero', 'Ferrán', 'Ferrández', 'Ferrándiz', 'Figueras', 'Figueroa', 'Figuerola',
        'Fiol', 'Flor', 'Flores', 'Folch', 'Fonseca', 'Font', 'Fortuny',
        'Franch', 'Francisco', 'Franco', 'Frutos', 'Frías', 'Fuente', 'Fuentes',
        'Fuertes', 'Fuster', 'Fábregas', 'Gabaldón', 'Galan', 'Galiano', 'Galindo',
        'Gallardo', 'Gallart', 'Gallego', 'Gallo', 'Galvez', 'Galván', 'Galán',
        'Garay', 'Garcia', 'Garcés', 'García', 'Gargallo', 'Garmendia', 'Garrido',
        'Garriga', 'Garzón', 'Gascón', 'Gaya', 'Gelabert', 'Gibert', 'Gil',
        'Gilabert', 'Gimenez', 'Gimeno', 'Giménez', 'Giner', 'Giralt', 'Girona',
        'Girón', 'Gisbert', 'Godoy', 'Goicoechea', 'Gomez', 'Gomila', 'Gomis',
        'Gonzalez', 'Gonzalo', 'González', 'Gordillo', 'Goñi', 'Gracia', 'Granados',
        'Grande', 'Gras', 'Grau', 'Gual', 'Guardia', 'Guardiola', 'Guerra',
        'Guerrero', 'Guijarro', 'Guillen', 'Guillén', 'Guitart', 'Gutierrez', 'Gutiérrez',
        'Guzman', 'Guzmán', 'Gálvez', 'Gámez', 'Gárate', 'Gómez', 'Haro',
        'Heras', 'Heredia', 'Hernandez', 'Hernando', 'Hernández', 'Herranz', 'Herrera',
        'Herrero', 'Hervia', 'Hervás', 'Hidalgo', 'Hierro', 'Higueras', 'Hoyos',
        'Hoz', 'Huerta', 'Huertas', 'Huguet', 'Hurtado', 'Ibarra', 'Ibañez',
        'Iborra', 'Ibáñez', 'Iglesia', 'Iglesias', 'Infante', 'Iniesta', 'Iriarte',
        'Isern', 'Izaguirre', 'Izquierdo', 'Iñiguez', 'Jara', 'Jaume', 'Jaén',
        'Jerez', 'Jimenez', 'Jiménez', 'Jordá', 'Jordán', 'Jove', 'Jover',
        'Juan', 'Juliá', 'Julián', 'Jurado', 'Juárez', 'Jáuregui', 'Jódar',
        'Lago', 'Laguna', 'Lamas', 'Landa', 'Lara', 'Larrañaga', 'Larrea',
        'Lasa', 'Lastra', 'Leal', 'Ledesma', 'Leiva', 'Leon', 'Lerma',
        'León', 'Lillo', 'Linares', 'Llabrés', 'Lladó', 'Llamas', 'Llano',
        'Llanos', 'Lledó', 'Llobet', 'Llopis', 'Llorens', 'Llorente', 'Lloret',
        'Lluch', 'Lobato', 'Lobo', 'Lopez', 'Lorenzo', 'Losa', 'Losada',
        'Lozano', 'Lucas', 'Lucena', 'Luján', 'Lumbreras', 'Luna', 'Luque',
        'Luz', 'Luís', 'López', 'Machado', 'Macias', 'Macías', 'Madrid',
        'Madrigal', 'Maestre', 'Maldonado', 'Malo', 'Mancebo', 'Manjón', 'Manrique',
        'Manso', 'Manuel', 'Manzanares', 'Manzano', 'Marco', 'Marcos', 'Marin',
        'Mariscal', 'Mariño', 'Marquez', 'Marqués', 'Marti', 'Martin', 'Martinez',
        'Martorell', 'Martí', 'Martín', 'Martínez', 'Marí', 'Marín', 'Mas',
        'Mascaró', 'Mata', 'Matas', 'Mate', 'Mateo', 'Mateos', 'Mateu',
        'Mayo', 'Mayol', 'Mayoral', 'Maza', 'Medina', 'Melero', 'Meléndez',
        'Mena', 'Mendez', 'Mendizábal', 'Mendoza', 'Menendez', 'Menéndez', 'Mercader',
        'Merino', 'Mesa', 'Miguel', 'Milla', 'Millán', 'Mir', 'Miralles',
        'Miranda', 'Miró', 'Moles', 'Molina', 'Moliner', 'Molins', 'Moll',
        'Monreal', 'Montalbán', 'Montaña', 'Montenegro', 'Montero', 'Montes', 'Montesinos',
        'Montoya', 'Montserrat', 'Mora', 'Moraleda', 'Morales', 'Morante', 'Morata',
        'Morcillo', 'Morell', 'Moreno', 'Morera', 'Morillo', 'Morán', 'Mosquera',
        'Moya', 'Mulet', 'Mur', 'Murcia', 'Murillo', 'Muro', 'Muñoz',
        'Mármol', 'Márquez', 'Méndez', 'Mínguez', 'Múgica', 'Múñiz', 'Nadal',
        'Naranjo', 'Narváez', 'Navarrete', 'Navarro', 'Navas', 'Nebot', 'Neira',
        'Nevado', 'Nicolau', 'Nicolás', 'Nieto', 'Niño', 'Nogueira', 'Noguera',
        'Nogués', 'Noriega', 'Novoa', 'Nuñez', 'Núñez', 'Ocaña', 'Ochoa',
        'Ojeda', 'Oliva', 'Olivares', 'Oliver', 'Olivera', 'Oliveras', 'Olivé',
        'Oller', 'Olmedo', 'Olmo', 'Ordóñez', 'Orozco', 'Ortega', 'Ortiz',
        'Ortuño', 'Osorio', 'Osuna', 'Otero', 'Pablo', 'Pacheco', 'Padilla',
        'Pagès', 'Palacio', 'Palacios', 'Palau', 'Pallarès', 'Palma', 'Palmer',
        'Palomar', 'Palomares', 'Palomino', 'Palomo', 'Paniagua', 'Pardo', 'Paredes',
        'Pareja', 'Parejo', 'Parra', 'Pascual', 'Pastor', 'Patiño', 'Pavón',
        'Paz', 'Pazos', 'Pedraza', 'Pedrero', 'Pedro', 'Pedrosa', 'Peinado',
        'Peiró', 'Pelayo', 'Pellicer', 'Peláez', 'Pera', 'Peral', 'Perales',
        'Peralta', 'Perea', 'Pereira', 'Perelló', 'Perera', 'Perez', 'Peña',
        'Peñalver', 'Peñas', 'Pi', 'Pina', 'Pineda', 'Pinedo', 'Pinilla',
        'Pino', 'Pinto', 'Pintor', 'Piquer', 'Pizarro', 'Piña', 'Piñeiro',
        'Piñol', 'Pla', 'Plana', 'Planas', 'Plaza', 'Pol', 'Polo',
        'Pomares', 'Pombo', 'Ponce', 'Pons', 'Pont', 'Porcel', 'Porras',
        'Porta', 'Portero', 'Portillo', 'Posada', 'Pou', 'Poza', 'Pozo',
        'Pozuelo', 'Prada', 'Prado', 'Prat', 'Prats', 'Priego', 'Prieto',
        'Puente', 'Puerta', 'Puga', 'Puig', 'Pujadas', 'Pujol', 'Pulido',
        'Páez', 'Pérez', 'Quero', 'Querol', 'Quesada', 'Quevedo', 'Quintana',
        'Quintanilla', 'Quintero', 'Quiroga', 'Quirós', 'Ramirez', 'Ramis', 'Ramos',
        'Ramírez', 'Ramón', 'Raya', 'Real', 'Rebollo', 'Recio', 'Redondo',
        'Reguera', 'Reig', 'Reina', 'Requena', 'Revilla', 'Rey', 'Reyes',
        'Riba', 'Ribas', 'Ribera', 'Ribes', 'Ricart', 'Rico', 'Riera',
        'Rincón', 'Rios', 'Ripoll', 'Riquelme', 'Rius', 'Rivas', 'Rivera',
        'Rivero', 'Robledo', 'Robles', 'Roca', 'Rocamora', 'Rocha', 'Roda',
        'Rodrigo', 'Rodriguez', 'Rodríguez', 'Roig', 'Rojas', 'Roldan', 'Roldán',
        'Roma', 'Roman', 'Romero', 'Romeu', 'Román', 'Ropero', 'Ros',
        'Rosa', 'Rosado', 'Rosales', 'Rosell', 'Roselló', 'Rosselló', 'Roura',
        'Rovira', 'Royo', 'Rozas', 'Ruano', 'Rubio', 'Rueda', 'Ruiz',
        'Río', 'Ríos', 'Ródenas', 'Saavedra', 'Sabater', 'Sacristán', 'Saez',
        'Sainz', 'Sala', 'Salamanca', 'Salas', 'Salazar', 'Salcedo', 'Saldaña',
        'Sales', 'Salgado', 'Salinas', 'Salmerón', 'Salom', 'Salvador', 'Salvà',
        'Samper', 'Sanabria', 'Sanchez', 'Sancho', 'Sandoval', 'Sanjuan', 'Sanmartín',
        'Sanmiguel', 'Sans', 'Santamaria', 'Santamaría', 'Santana', 'Santiago', 'Santos',
        'Sanz', 'Sarabia', 'Sarmiento', 'Sastre', 'Saura', 'Sebastián', 'Seco',
        'Sedano', 'Segarra', 'Segovia', 'Segura', 'Seguí', 'Serna', 'Serra',
        'Serrano', 'Sevilla', 'Sevillano', 'Sierra', 'Silva', 'Simó', 'Sobrino',
        'Sola', 'Solana', 'Solano', 'Soler', 'Solera', 'Solsona', 'Solé',
        'Solís', 'Somoza', 'Soria', 'Soriano', 'Sosa', 'Sotelo', 'Soto',
        'Suarez', 'Sureda', 'Suárez', 'Sáenz', 'Sáez', 'Sánchez', 'Taboada',
        'Talavera', 'Tamarit', 'Tamayo', 'Tapia', 'Tejada', 'Tejedor', 'Tejera',
        'Tejero', 'Tello', 'Tena', 'Tenorio', 'Terrón', 'Teruel', 'Tirado',
        'Toledo', 'Tolosa', 'Tomas', 'Tomás', 'Tomé', 'Tormo', 'Toro',
        'Torralba', 'Torre', 'Torrecilla', 'Torrens', 'Torrent', 'Torrents', 'Torres',
        'Torrijos', 'Tovar', 'Trillo', 'Trujillo', 'Tudela', 'Tur', 'Téllez',
        'Ugarte', 'Ureña', 'Uriarte', 'Uribe', 'Urrutia', 'Uría', 'Valbuena',
        'Valcárcel', 'Valderrama', 'Valdés', 'Valencia', 'Valenciano', 'Valentín', 'Valenzuela',
        'Valera', 'Valero', 'Vall', 'Valle', 'Vallejo', 'Valls', 'Vallés',
        'Valverde', 'Vaquero', 'Vara', 'Varela', 'Vargas', 'Vazquez', 'Vega',
        'Velasco', 'Velázquez', 'Vendrell', 'Vera', 'Verdejo', 'Verdugo', 'Verdú',
        'Vergara', 'Viana', 'Vicens', 'Vicente', 'Vidal', 'Vigil', 'Vila',
        'Vilalta', 'Vilanova', 'Vilaplana', 'Vilar', 'Villa', 'Villalba', 'Villalobos',
        'Villalonga', 'Villanueva', 'Villar', 'Villaverde', 'Villegas', 'Villena', 'Vives',
        'Vizcaíno', 'Viña', 'Viñas', 'Vázquez', 'Vélez', 'Yuste', 'Yáñez',
        'Zabala', 'Zabaleta', 'Zamora', 'Zamorano', 'Zapata', 'Zaragoza', 'Zorrilla',
        'Zurita', 'Águila', 'Álamo', 'Álvarez', 'Álvaro', 'Ángel', 'Ávila',
    )

    prefixes = ('de', 'del')

    # https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    language_names = [
        'Afar', 'Abjasio', 'Avéstico', 'Africaans', 'Akánico', 'Amhárico',
        'Aragonés', 'Arábico', 'Asamés', 'Avar', 'Aimara', 'Azerí',
        'Baskir', 'Bielorruso', 'Búlgaro', 'lenguas Bihari', 'Bislama',
        'Bambara', 'Bengalí', 'Tibetano', 'Bretón', 'Bosnio', 'Catalán',
        'Checheno', 'Chamorro', 'Corso', 'Cree', 'Checo', 'Eslavo eclesiástico',
        'Chuvasio', 'Galés', 'Danés', 'Alemán', 'Maldivo', 'Dzongkha', 'Ewé',
        'Griego', 'Inglés', 'Esperanto', 'Español', 'Estonio', 'Vasco',
        'Persa', 'Fula', 'Finés', 'Fiyiano', 'Feroés', 'Francés',
        'lenguas Frisonas', 'Irlandés', 'Gaélico', 'Gallego', 'Guaraní',
        'Gujarati', 'Manés', 'Hausa', 'Hebreo', 'Hindú', 'Hiri Motu',
        'Croata', 'Haitiano', 'Húngaro', 'Armenio', 'Herero',
        'Interlingua', 'Indonés', 'Igbo', 'Nuosu', 'lenguas esquimales',
        'Ido', 'Islandés', 'Italiano', 'Inuit', 'Japonés', 'Javanés',
        'Georgiano', 'Congolés', 'Kikuyu', 'Kuanyama', 'Kazajo',
        'Groenlandés', 'Camboyano', 'Canarés', 'Coreano', 'Kanurí',
        'Kashmiri Masala', 'Kurdo', 'Komi', 'Córnico', 'Kirguís', 'Latín',
        'Luxemburgués', 'Luganda', 'Limburgués', 'Lingala', 'Lao',
        'Lituano', 'Kiluba', 'Letón', 'Malgache', 'Marshalés', 'Maorí',
        'Macedonio', 'Malabar', 'Mongol', 'Marathí', 'Malayo', 'Maltés',
        'Birmano', 'Nauru', 'Ndebele norte', 'Nepalí', 'Ndonga',
        'Neerlandés', 'Nuevo Noruego', 'Noruego', 'Ndebele sur',
        'Navajo', 'Chichewa', 'Occitano', 'Ojibwa', 'Oromo', 'Oriya',
        'Osetio', 'Panyabí', 'Pali', 'Polaco', 'Pastún', 'Portugués',
        'Quechua', 'Romanche', 'Rundi', 'Rumano', 'Ruso', 'Kiñaruanda',
        'Sánscrito', 'Sardo', 'Sindi', 'Sami septentrional', 'Sango',
        'Cingalés', 'Eslovaco', 'Samoano', 'Shona', 'Somalí', 'Albanés',
        'Serbio', 'Suazi', 'Sesoto', 'Sondanés', 'Sueco', 'Swahili',
        'Tamil', 'Télugu', 'Takiyo', 'Tailandés', 'Tigriña', 'Turcomano',
        'Tagalo', 'Setsuana', 'Tongoano', 'Turco', 'Tsonga', 'Tártaro',
        'Tahitiano', 'Uigur', 'Ucraniano', 'Urdu', 'Uzbeko', 'Venda',
        'Vietnamita', 'Valón', 'Wólof', 'Xhosa', 'Yidis', 'Yoruba',
        'Zhuang', 'Chino', 'Zulú',
    ]
