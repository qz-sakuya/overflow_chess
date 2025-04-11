import pygame
import numpy as np

# 基本设置
WHITE, BLACK, PLAYER_COLORS = 100, 0, [1, 2, 3, 4]
REPETITIVE_SEARCH_STEPS = 2


class ChessBoard:
    def __init__(self, size):
        self.size = size
        self.state = np.full((self.size, self.size), WHITE)
        self.state_stack = []

    def save_state(self):
        self.state_stack.append(np.copy(self.state))

    def undo_state(self):
        if len(self.state_stack) >= 1:
            self.state = np.copy(self.state_stack[-1])
            self.state_stack.pop()

    def place_colour(self, x, y, colour):
        if x not in range(0, self.size) or y not in range(0, self.size):
            return False
        if colour not in range(1, 5):
            return False
        if self.state[y, x] != WHITE:  # 检查是否为白色方块
            return False

        self.state[y, x] = colour
        return True

    def push(self, direction, n):
        if direction not in range(0, 4) or n not in range(0, self.size):
            return False

        # 检查是否有阻挡方块，并且至少有一个非阻挡和非空方块
        if direction in [0, 1]:  # 上下方向，检查列
            col = self.state[:, n]
            if any(-4 <= x <= -1 for x in col):  # 如果存在阻挡方块
                return False
            if all(x == 0 or -4 <= x <= -1 for x in col):  # 如果没有颜色方块
                return False
            if direction == 0:  # 向上
                new_col = np.roll(col, -1)
                new_col[-1] = BLACK
                self.state[:, n] = new_col
            else:  # 向下
                new_col = np.roll(col, 1)
                new_col[0] = BLACK
                self.state[:, n] = new_col
        else:  # 左右方向，检查行
            row = self.state[n, :]
            if any(-4 <= x <= -1 for x in row):  # 如果存在阻挡方块
                return False
            if all(x == 0 or -4 <= x <= -1 for x in row):  # 如果没有颜色方块
                return False
            if direction == 2:  # 向左
                new_row = np.roll(row, -1)
                new_row[-1] = BLACK
                self.state[n, :] = new_row
            else:  # 向右
                new_row = np.roll(row, 1)
                new_row[0] = BLACK
                self.state[n, :] = new_row

        return True

    def place_barrier(self, x, y, colour):
        if x not in range(0, self.size) or y not in range(0, self.size):
            return False
        if colour not in range(1, 5):
            return False
        if self.state[y, x] != BLACK:
            return False
        self.delete_barrier(colour)
        self.state[y, x] = -colour
        return True

    def delete_barrier(self, colour):
        if colour not in range(1, 5):
            return False
        for i in range(self.size):
            for j in range(self.size):
                if self.state[i, j] == -colour:
                    self.state[i, j] = BLACK

    def reset(self, size, num_players):
        self.size = size
        self.state = np.full((self.size, self.size), WHITE)
        if self.size % num_players == 1:
            self.state[self.size // 2, self.size // 2] = BLACK
        self.state_stack.clear()

    def judge_alive(self, colour):
        return np.any(self.state == colour)

    def place_phase_finish(self):
        return not np.any(self.state == WHITE)

    def no_repetition(self, step):
        current_state = self.get_chess_board()
        for i in range(step):
            if len(self.state_stack) > i and np.array_equal(current_state, self.state_stack[-i - 1]):
                self.state = np.copy(self.state_stack[-1])
                return False
        return True

    def get_chess_board(self):
        return np.copy(self.state)


class GameUI:
    def __init__(self):
        pygame.init()
        self.size = 7
        self.board = ChessBoard(self.size)
        self.players = [-1] * 4  # 初始化玩家状态数组
        self.current_player_id = 0  # 范围0-3
        self.current_phase = 0  # 范围0-1
        self.turn_count = 0  # 从0开始
        self.game_over = False
        self.restart = False
        self.info_text = ''
        self.screen = pygame.display.set_mode((800, 450))
        self.font = pygame.font.Font(None, 28)  # 设置字号

    def render(self):
        # 更改背景颜色为橙色
        self.screen.fill((255, 153, 51))

        # 渲染棋盘
        for y in range(self.size):
            for x in range(self.size):
                value = self.board.get_chess_board()[y, x]

                rect_x, rect_y = x * 50 + 50, y * 50 + 50

                if value < 0:  # 阻挡方块
                    color = self.get_color(-value)
                    # 绘制边框
                    pygame.draw.rect(self.screen, (0, 0, 0), (rect_x, rect_y, 50, 50), 1)  # 黑色边框
                    # 绘制内部颜色
                    pygame.draw.rect(self.screen, (80, 80, 80), (rect_x + 1, rect_y + 1, 48, 48))
                    pygame.draw.rect(self.screen, color, (rect_x + 9, rect_y + 9, 32, 32))
                    pygame.draw.rect(self.screen, (80, 80, 80), (rect_x + 14, rect_y + 14, 22, 22))

                else:  # 非阻挡方块
                    color = self.get_color(value)
                    # 绘制边框
                    pygame.draw.rect(self.screen, (0, 0, 0), (rect_x, rect_y, 50, 50), 1)  # 黑色边框
                    # 绘制内部颜色
                    pygame.draw.rect(self.screen, color, (rect_x + 1, rect_y + 1, 48, 48))

        # 渲染推动按钮
        for i in range(self.size):
            self.render_push_button("up", i, self.size)
            self.render_push_button("down", i, self.size)
            self.render_push_button("left", i, self.size)
            self.render_push_button("right", i, self.size)

        # 渲染玩家状态，并为每个玩家状态添加边框
        for i in range(4):
            player_color = self.get_color(i + 1)
            rect_x, rect_y = 600, i * 50 + 50
            pygame.draw.rect(self.screen, (0, 0, 0), (rect_x, rect_y, 50, 50), 1)
            pygame.draw.rect(self.screen, player_color, (rect_x + 1, rect_y + 1, 48, 48))

            status_symbol = "N/P" if self.players[i] == -1 else "Out" if self.players[i] == 0 else "Alive"
            text = self.font.render(status_symbol, True, (0, 0, 0))
            self.screen.blit(text, (660, i * 50 + 60))

        # 显示当前操作玩家
        current_player_text = self.font.render("Current Player:", True, (0, 0, 0))
        self.screen.blit(current_player_text, (600, 290))

        rect_x, rect_y = 600, 330
        pygame.draw.rect(self.screen, (0, 0, 0), (rect_x, rect_y, 50, 50), 1)
        pygame.draw.rect(self.screen, self.get_color(self.current_player_id + 1), (rect_x + 1, rect_y + 1, 48, 48))

        # 显示当前阶段
        phase_text = "Placement Phase . . ." if self.current_phase == 0 else "Overflow Phase!"
        phase_render = self.font.render(phase_text, True, (0, 0, 0))
        self.screen.blit(phase_render, (600, 400))

        # 显示提示信息
        phase_render = self.font.render(self.info_text, True, (0, 0, 0))
        self.screen.blit(phase_render, (475, 17.5))

        # 添加“撤销”和“重启”按钮
        button_width, button_height = 100, 50
        self.undo_button_rect = pygame.Rect(475, 330, button_width, button_height)
        self.restart_button_rect = pygame.Rect(475, 385, button_width, button_height)

        pygame.draw.rect(self.screen, (0, 0, 0), self.undo_button_rect, 2)  # 黑色边框
        pygame.draw.rect(self.screen, (200, 200, 200),
                         (self.undo_button_rect.x + 2, self.undo_button_rect.y + 2,
                          self.undo_button_rect.width - 4, self.undo_button_rect.height - 4))  # 按钮内部颜色

        pygame.draw.rect(self.screen, (0, 0, 0), self.restart_button_rect, 2)  # 黑色边框
        pygame.draw.rect(self.screen, (200, 200, 200),
                         (self.restart_button_rect.x + 2, self.restart_button_rect.y + 2,
                          self.restart_button_rect.width - 4, self.restart_button_rect.height - 4))  # 按钮内部颜色

        undo_text = self.font.render("Undo", True, (0, 0, 0))  # 绘制按钮文本
        restart_text = self.font.render("Restart", True, (0, 0, 0))

        self.screen.blit(undo_text, (self.undo_button_rect.x + 20, self.undo_button_rect.y + 15))
        self.screen.blit(restart_text, (self.restart_button_rect.x + 15, self.restart_button_rect.y + 15))

        pygame.display.flip()

    # 获取对应标识色
    def get_color(self, value):
        if value == WHITE:
            return (250, 250, 250)
        elif value == BLACK:
            return (40, 40, 40)
        elif value in PLAYER_COLORS:
            color_map = {1: (200, 60, 60),  # 红色
                         2: (255, 210, 60),  # 黄色
                         3: (60, 120, 255),  # 蓝色
                         4: (60, 200, 60)}  # 绿色
            return color_map[value]
        elif value < 0:
            return (128, 128, 128)  # 阻挡方块颜色
        return (255, 255, 255)

    # 绘制推动按钮
    def render_push_button(self, direction, n, board_size):
        # 计算棋盘的实际宽度和高度
        cell_size = 50  # 每个格子的大小
        board_width = board_height = board_size * cell_size

        button_rects = {
            "up": ((n * cell_size + cell_size, 0, cell_size, cell_size), (n * cell_size + cell_size + 25, 25)),
            "down": ((n * cell_size + cell_size, board_height + cell_size, cell_size, cell_size),
                     (n * cell_size + cell_size + 25, board_height + cell_size + 25)),
            "left": ((0, n * cell_size + cell_size, cell_size, cell_size), (25, n * cell_size + cell_size + 25)),
            "right": ((board_width + cell_size, n * cell_size + cell_size, cell_size, cell_size),
                      (board_width + cell_size + 25, n * cell_size + cell_size + 25))
        }

        rect, triangle_pos = button_rects[direction]

        # 绘制边框
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
        # 绘制内部灰色部分
        pygame.draw.rect(self.screen, (128, 128, 128), (rect[0] + 1, rect[1] + 1, 48, 48))

        points = {
            "up": [(triangle_pos[0] - 10, triangle_pos[1] - 15), (triangle_pos[0] + 10, triangle_pos[1] - 15),
                   (triangle_pos[0], triangle_pos[1] + 10)],
            "down": [(triangle_pos[0] - 10, triangle_pos[1] + 15), (triangle_pos[0] + 10, triangle_pos[1] + 15),
                     (triangle_pos[0], triangle_pos[1] - 10)],
            "left": [(triangle_pos[0] - 15, triangle_pos[1] + 10), (triangle_pos[0] - 15, triangle_pos[1] - 10),
                     (triangle_pos[0] + 10, triangle_pos[1])],
            "right": [(triangle_pos[0] + 15, triangle_pos[1] + 10), (triangle_pos[0] + 15, triangle_pos[1] - 10),
                      (triangle_pos[0] - 10, triangle_pos[1])]
        }

        # 调整三角形方向
        pygame.draw.polygon(self.screen, (0, 0, 0), points[direction])

    def game_loop(self):
        self.restart = True
        while True:
            if self.restart:
                self.start()  # 重启状态则调用重启
                self.restart = False
            self.board.save_state()
            self.info_text = ''

            if self.current_phase == 0:  # 放置阶段
                # 循环检测操作
                success = False
                while not success:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return

                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            pos = pygame.mouse.get_pos()
                            # 先处理撤销和重启按钮
                            if self.undo_button_rect.collidepoint(pos):
                                self.undo()
                                success = True
                            elif self.restart_button_rect.collidepoint(pos):
                                self.restart = True  # 进入重启状态
                                success = True
                            # 游戏结束后不能操作
                            elif not self.game_over:
                                x, y = pos[0] // 50 - 1, pos[1] // 50 - 1  # 换算坐标
                                if self.board.place_colour(x, y, self.current_player_id + 1):  # 放置颜色方块
                                    success = True

                # 检测放置阶段是否结束
                if self.board.place_phase_finish():
                    self.current_phase = 1

            else:  # 溢出阶段
                # 循环检测操作
                success = False
                while not success:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            return

                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            pos = pygame.mouse.get_pos()
                            # 先处理撤销和重启按钮
                            if self.undo_button_rect.collidepoint(pos):
                                self.undo()
                                success = True
                            elif self.restart_button_rect.collidepoint(pos):
                                self.restart = True  # 进入重启状态
                                success = True
                            # 游戏结束后不能操作
                            elif not self.game_over:
                                x, y = pos[0] // 50 - 1, pos[1] // 50 - 1  # 换算坐标

                                if y == self.size:  # 朝上推动
                                    if self.board.push(0, x):
                                        success = True
                                elif y == -1:  # 朝下推动
                                    if self.board.push(1, x):
                                        success = True
                                elif x == self.size:  # 朝左推动
                                    if self.board.push(2, y):
                                        success = True
                                elif x == -1:  # 朝右推动
                                    if self.board.push(3, y):
                                        success = True
                                elif self.board.place_barrier(x, y, self.current_player_id + 1):  # 放置阻挡方块
                                    success = True

                                if not self.board.no_repetition(REPETITIVE_SEARCH_STEPS) and success is True:
                                    self.info_text = 'No repetition of positions allowed'
                                    self.render()
                                    self.info_text = ''
                                    success = False

                # 检测玩家存活状态
                alive_players = []  # 存储存活玩家ID
                for player_id, status in enumerate(self.players):
                    if self.players[player_id] != -1 and not self.board.judge_alive(player_id + 1):  # 如果玩家被淘汰
                        self.players[player_id] = 0  # 标记为淘汰
                        self.board.delete_barrier(player_id + 1)  # 删除其阻挡方块
                    elif status == 1:  # 如果玩家仍然存活
                        alive_players.append(player_id + 1)

                # 检查是否有玩家获胜
                if len(alive_players) == 1:  # 如果只有一个存活玩家
                    winner = alive_players[0]
                    self.info_text = "WIN: Player{}".format(winner)
                    self.game_over = True

            if not self.game_over:
                self.next_player()
                self.turn_count += 1
            self.render()

    # 获取下一位玩家
    def next_player(self):
        self.current_player_id = (self.current_player_id + 1) % 4
        while self.players[self.current_player_id] != 1:
            self.current_player_id = (self.current_player_id + 1) % 4

    # 获取上一位玩家
    def previous_player(self):
        self.current_player_id = (self.current_player_id - 1) % 4
        while self.players[self.current_player_id] != 1:
            self.current_player_id = (self.current_player_id - 1) % 4

    def start(self):
        # 清除所有玩家状态
        for i in range(len(self.players)):
            self.players[i] = -1

        # 第一步：选择玩家人数
        button_width, button_height = 100, 50
        buttons_players = [
            pygame.Rect(200, 200, button_width, button_height),  # 2 players
            pygame.Rect(350, 200, button_width, button_height),  # 3 players
            pygame.Rect(500, 200, button_width, button_height)  # 4 players
        ]

        num_players = 0
        waiting_for_selection = True
        while waiting_for_selection:
            self.screen.fill((255, 153, 51))  # 背景颜色

            # 绘制按钮
            for i, button_rect in enumerate(buttons_players):
                pygame.draw.rect(self.screen, (200, 200, 200), button_rect)  # 按钮背景色
                pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)  # 黑色边框
                text_surface = self.font.render("{} Players".format(i + 2), True, (0, 0, 0))
                self.screen.blit(text_surface, (button_rect.x + 8, button_rect.y + 15))

            pygame.display.flip()

            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()  # 获取鼠标点击位置
                    for i, button_rect in enumerate(buttons_players):
                        if button_rect.collidepoint(pos):
                            num_players = i + 2  # 根据点击的按钮设置玩家数量
                            waiting_for_selection = False
                            break

        # 第二步：选择棋盘大小
        button_width, button_height = 120, 50
        buttons_size = [
            pygame.Rect(190, 200, button_width, button_height),  # 5x5 board
            pygame.Rect(340, 200, button_width, button_height),  # 6x6 board
            pygame.Rect(490, 200, button_width, button_height)  # 7x7 board
        ]

        size = 0
        waiting_for_selection = True
        while waiting_for_selection:
            self.screen.fill((255, 153, 51))  # 背景颜色

            # 绘制按钮
            for i, button_rect in enumerate(buttons_size):
                pygame.draw.rect(self.screen, (200, 200, 200), button_rect)  # 按钮背景色
                pygame.draw.rect(self.screen, (0, 0, 0), button_rect, 2)  # 黑色边框
                text_surface = self.font.render("{}x{} Board".format(i + 5, i + 5), True, (0, 0, 0))
                self.screen.blit(text_surface, (button_rect.x + 12, button_rect.y + 15))

            pygame.display.flip()

            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()  # 获取鼠标点击位置
                    for i, button_rect in enumerate(buttons_size):
                        if button_rect.collidepoint(pos):
                            size = i + 5  # 根据点击的按钮设置棋盘大小
                            waiting_for_selection = False
                            break

        # 设置玩家状态
        for i in range(num_players):
            self.players[i] = 1  # 玩家存活

        # 重置游戏状态
        self.size = size
        self.board.reset(self.size, num_players)
        self.current_player_id = 0
        self.current_phase = 0
        self.turn_count = 0
        self.game_over = False
        self.restart = True  # 进入重启状态
        self.info_text = ''

        # 绘制初始状态
        self.render()

    def undo(self):
        self.board.undo_state()  # 额外出栈一次，因为主循环每次开始时，入栈了一次
        self.previous_player()  # 额外后退一位，因为主循环每次最后时，玩家前进了一位
        self.turn_count -= 1  # 额外减一步，因为主循环每次最后时，加了一步

        if self.turn_count < 0:
            return False
        self.board.undo_state()
        self.previous_player()
        self.turn_count -= 1
        self.game_over = False

        # 恢复玩家存活状态
        for player_id, status in enumerate(self.players):
            if self.board.judge_alive(player_id + 1):
                self.players[player_id] = 1  # 标记为存活

        # 检测阶段
        if not self.board.place_phase_finish():
            self.current_phase = 0


def run_game():
    game_ui = GameUI()
    game_ui.game_loop()


if __name__ == '__main__':
    run_game()
