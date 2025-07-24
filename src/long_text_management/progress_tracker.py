"""
Progress Tracker and State Manager
进度跟踪器和状态管理器

提供红楼梦后40回续写的完整进度跟踪和状态管理功能。
"""

import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time

class ProjectStatus(Enum):
    """项目状态枚举"""
    NOT_STARTED = "未开始"
    PLANNING = "规划中"
    WRITING = "续写中"
    REVIEWING = "审查中"
    COMPLETED = "已完成"
    PAUSED = "暂停"
    ERROR = "错误"

class ChapterStatus(Enum):
    """章节状态枚举"""
    NOT_STARTED = "未开始"
    PLANNED = "已规划"
    EXTRACTING = "状态提取中"
    WRITING = "续写中"
    REVIEWING = "审查中"
    COMPLETED = "已完成"
    FAILED = "失败"

@dataclass
class ChapterProgress:
    """章节进度数据"""
    chapter_number: int
    title: str
    status: ChapterStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    word_count: int = 0
    estimated_words: int = 0
    completion_percentage: float = 0.0
    iterations: int = 0
    last_updated: datetime = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        result['status'] = self.status.value
        if self.start_time:
            result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        if self.last_updated:
            result['last_updated'] = self.last_updated.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChapterProgress':
        """从字典创建实例"""
        data = data.copy()
        data['status'] = ChapterStatus(data['status'])
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        if data.get('last_updated'):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)

@dataclass 
class ProjectStatistics:
    """项目统计数据"""
    total_chapters: int = 40
    completed_chapters: int = 0
    in_progress_chapters: int = 0
    planned_chapters: int = 0
    total_words: int = 0
    estimated_total_words: int = 491000
    overall_completion: float = 0.0
    estimated_completion_date: Optional[datetime] = None
    average_words_per_chapter: float = 0.0
    average_time_per_chapter: Optional[timedelta] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        if self.estimated_completion_date:
            result['estimated_completion_date'] = self.estimated_completion_date.isoformat()
        if self.average_time_per_chapter:
            result['average_time_per_chapter'] = str(self.average_time_per_chapter)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectStatistics':
        """从字典创建实例"""
        data = data.copy()
        if data.get('estimated_completion_date'):
            data['estimated_completion_date'] = datetime.fromisoformat(data['estimated_completion_date'])
        if data.get('average_time_per_chapter'):
            data['average_time_per_chapter'] = timedelta(seconds=float(data['average_time_per_chapter'].split(':')[-1]))
        return cls(**data)

@dataclass
class ProjectState:
    """完整项目状态"""
    project_status: ProjectStatus
    start_date: datetime
    last_updated: datetime
    chapters: Dict[int, ChapterProgress]
    statistics: ProjectStatistics
    current_chapter: Optional[int] = None
    session_start: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'project_status': self.project_status.value,
            'start_date': self.start_date.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'chapters': {str(k): v.to_dict() for k, v in self.chapters.items()},
            'statistics': self.statistics.to_dict(),
            'current_chapter': self.current_chapter,
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectState':
        """从字典创建实例"""
        return cls(
            project_status=ProjectStatus(data['project_status']),
            start_date=datetime.fromisoformat(data['start_date']),
            last_updated=datetime.fromisoformat(data['last_updated']),
            chapters={int(k): ChapterProgress.from_dict(v) for k, v in data['chapters'].items()},
            statistics=ProjectStatistics.from_dict(data['statistics']),
            current_chapter=data.get('current_chapter'),
            session_start=datetime.fromisoformat(data['session_start']) if data.get('session_start') else None,
            notes=data.get('notes', '')
        )

class ProgressTracker:
    """进度跟踪器和状态管理器"""
    
    def __init__(self, state_file: str = "data/processed/project_state.json"):
        """
        初始化进度跟踪器
        
        Args:
            state_file: 状态文件路径
        """
        self.state_file = state_file
        self.project_state: Optional[ProjectState] = None
        self._ensure_state_dir()
        
    def _ensure_state_dir(self):
        """确保状态文件目录存在"""
        state_dir = os.path.dirname(self.state_file)
        if state_dir:  # 只有当目录不为空时才创建
            os.makedirs(state_dir, exist_ok=True)
    
    def initialize_project(self, force: bool = False) -> ProjectState:
        """
        初始化项目状态
        
        Args:
            force: 是否强制重新初始化
            
        Returns:
            初始化的项目状态
        """
        if not force and os.path.exists(self.state_file):
            try:
                return self.load_state()
            except Exception as e:
                print(f"加载状态失败，将重新初始化: {e}")
        
        # 创建初始章节进度
        chapters = {}
        for chapter_num in range(81, 121):  # 第81-120回
            chapters[chapter_num] = ChapterProgress(
                chapter_number=chapter_num,
                title=f"第{chapter_num}回",
                status=ChapterStatus.NOT_STARTED,
                estimated_words=12275,  # 平均每回字数
                last_updated=datetime.now()
            )
        
        # 创建项目状态
        self.project_state = ProjectState(
            project_status=ProjectStatus.NOT_STARTED,
            start_date=datetime.now(),
            last_updated=datetime.now(),
            chapters=chapters,
            statistics=ProjectStatistics(),
            notes="红楼梦后40回续写项目初始化"
        )
        
        self.save_state()
        return self.project_state
    
    def load_state(self) -> ProjectState:
        """
        加载项目状态
        
        Returns:
            加载的项目状态
        """
        if not os.path.exists(self.state_file):
            return self.initialize_project()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.project_state = ProjectState.from_dict(data)
                return self.project_state
        except Exception as e:
            print(f"加载状态文件失败: {e}")
            return self.initialize_project()
    
    def save_state(self):
        """保存项目状态"""
        if not self.project_state:
            return
        
        self.project_state.last_updated = datetime.now()
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_state.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存状态文件失败: {e}")
    
    def start_session(self):
        """开始工作会话"""
        if not self.project_state:
            self.load_state()
        
        self.project_state.session_start = datetime.now()
        if self.project_state.project_status == ProjectStatus.NOT_STARTED:
            self.project_state.project_status = ProjectStatus.WRITING
        
        self.save_state()
    
    def end_session(self):
        """结束工作会话"""
        if not self.project_state:
            return
        
        self.project_state.session_start = None
        self.save_state()
    
    def start_chapter(self, chapter_number: int, title: str = "") -> bool:
        """
        开始章节续写
        
        Args:
            chapter_number: 章节编号
            title: 章节标题
            
        Returns:
            是否成功开始
        """
        if not self.project_state:
            self.load_state()
        
        if chapter_number not in self.project_state.chapters:
            print(f"章节{chapter_number}不在规划范围内")
            return False
        
        chapter = self.project_state.chapters[chapter_number]
        chapter.status = ChapterStatus.WRITING
        chapter.start_time = datetime.now()
        chapter.last_updated = datetime.now()
        
        if title:
            chapter.title = title
        
        self.project_state.current_chapter = chapter_number
        self.project_state.project_status = ProjectStatus.WRITING
        
        self.save_state()
        return True
    
    def update_chapter_progress(self, chapter_number: int, 
                              word_count: int = None,
                              completion_percentage: float = None,
                              status: ChapterStatus = None,
                              notes: str = None) -> bool:
        """
        更新章节进度
        
        Args:
            chapter_number: 章节编号
            word_count: 当前字数
            completion_percentage: 完成百分比
            status: 章节状态
            notes: 备注
            
        Returns:
            是否成功更新
        """
        if not self.project_state:
            self.load_state()
        
        if chapter_number not in self.project_state.chapters:
            return False
        
        chapter = self.project_state.chapters[chapter_number]
        
        if word_count is not None:
            chapter.word_count = word_count
        
        if completion_percentage is not None:
            chapter.completion_percentage = min(100.0, max(0.0, completion_percentage))
        
        if status is not None:
            chapter.status = status
            if status == ChapterStatus.COMPLETED:
                chapter.end_time = datetime.now()
                chapter.completion_percentage = 100.0
        
        if notes is not None:
            chapter.notes = notes
        
        chapter.last_updated = datetime.now()
        
        # 自动计算完成百分比
        if word_count and chapter.estimated_words > 0:
            auto_percentage = (word_count / chapter.estimated_words) * 100
            chapter.completion_percentage = min(100.0, auto_percentage)
        
        self._update_statistics()
        self.save_state()
        return True
    
    def complete_chapter(self, chapter_number: int, final_word_count: int = None) -> bool:
        """
        完成章节
        
        Args:
            chapter_number: 章节编号
            final_word_count: 最终字数
            
        Returns:
            是否成功完成
        """
        if not self.project_state:
            self.load_state()
        
        if chapter_number not in self.project_state.chapters:
            return False
        
        chapter = self.project_state.chapters[chapter_number]
        chapter.status = ChapterStatus.COMPLETED
        chapter.end_time = datetime.now()
        chapter.completion_percentage = 100.0
        chapter.last_updated = datetime.now()
        
        if final_word_count:
            chapter.word_count = final_word_count
        
        # 检查是否完成所有章节
        all_completed = all(
            ch.status == ChapterStatus.COMPLETED 
            for ch in self.project_state.chapters.values()
        )
        
        if all_completed:
            self.project_state.project_status = ProjectStatus.COMPLETED
        
        self._update_statistics()
        self.save_state()
        return True
    
    def _update_statistics(self):
        """更新项目统计数据"""
        if not self.project_state:
            return
        
        stats = self.project_state.statistics
        chapters = self.project_state.chapters.values()
        
        # 基本统计
        stats.completed_chapters = sum(1 for ch in chapters if ch.status == ChapterStatus.COMPLETED)
        stats.in_progress_chapters = sum(1 for ch in chapters if ch.status in [ChapterStatus.WRITING, ChapterStatus.REVIEWING])
        stats.planned_chapters = sum(1 for ch in chapters if ch.status == ChapterStatus.PLANNED)
        
        # 字数统计
        stats.total_words = sum(ch.word_count for ch in chapters)
        
        # 完成度计算
        if stats.total_chapters > 0:
            stats.overall_completion = (stats.completed_chapters / stats.total_chapters) * 100
        
        # 平均字数计算
        completed_chapters = [ch for ch in chapters if ch.status == ChapterStatus.COMPLETED and ch.word_count > 0]
        if completed_chapters:
            stats.average_words_per_chapter = sum(ch.word_count for ch in completed_chapters) / len(completed_chapters)
        
        # 预估完成时间
        self._estimate_completion_date()
    
    def _estimate_completion_date(self):
        """预估完成时间"""
        if not self.project_state:
            return
        
        completed_chapters = [
            ch for ch in self.project_state.chapters.values() 
            if ch.status == ChapterStatus.COMPLETED and ch.start_time and ch.end_time
        ]
        
        if len(completed_chapters) < 2:
            return
        
        # 计算平均完成时间
        total_time = sum(
            (ch.end_time - ch.start_time).total_seconds() 
            for ch in completed_chapters
        )
        avg_time_seconds = total_time / len(completed_chapters)
        self.project_state.statistics.average_time_per_chapter = timedelta(seconds=avg_time_seconds)
        
        # 预估剩余时间
        remaining_chapters = 40 - self.project_state.statistics.completed_chapters
        if remaining_chapters > 0:
            remaining_time = timedelta(seconds=avg_time_seconds * remaining_chapters)
            self.project_state.statistics.estimated_completion_date = datetime.now() + remaining_time
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        获取进度摘要
        
        Returns:
            进度摘要字典
        """
        if not self.project_state:
            self.load_state()
        
        stats = self.project_state.statistics
        
        return {
            "项目状态": self.project_state.project_status.value,
            "总体进度": f"{stats.overall_completion:.1f}%",
            "完成章节": f"{stats.completed_chapters}/{stats.total_chapters}",
            "当前章节": self.project_state.current_chapter,
            "总字数": f"{stats.total_words:,}",
            "预估总字数": f"{stats.estimated_total_words:,}",
            "完成字数比例": f"{(stats.total_words/stats.estimated_total_words*100):.1f}%" if stats.estimated_total_words > 0 else "0%",
            "平均每章字数": f"{stats.average_words_per_chapter:.0f}" if stats.average_words_per_chapter > 0 else "暂无数据",
            "预估完成时间": stats.estimated_completion_date.strftime("%Y-%m-%d") if stats.estimated_completion_date else "暂无数据",
            "最后更新": self.project_state.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_chapter_list(self, status_filter: ChapterStatus = None) -> List[Dict[str, Any]]:
        """
        获取章节列表
        
        Args:
            status_filter: 状态过滤器
            
        Returns:
            章节列表
        """
        if not self.project_state:
            self.load_state()
        
        chapters = []
        for chapter in sorted(self.project_state.chapters.values(), key=lambda x: x.chapter_number):
            if status_filter and chapter.status != status_filter:
                continue
                
            chapters.append({
                "章节": f"第{chapter.chapter_number}回",
                "标题": chapter.title,
                "状态": chapter.status.value,
                "进度": f"{chapter.completion_percentage:.1f}%",
                "字数": f"{chapter.word_count}/{chapter.estimated_words}",
                "最后更新": chapter.last_updated.strftime("%Y-%m-%d %H:%M") if chapter.last_updated else "未开始"
            })
        
        return chapters
    
    def generate_progress_report(self, output_file: str = None) -> str:
        """
        生成进度报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            报告内容
        """
        if not self.project_state:
            self.load_state()
        
        summary = self.get_progress_summary()
        chapters = self.get_chapter_list()
        
        report_lines = [
            "# 红楼梦后40回续写进度报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 项目概览",
            "",
            f"- **项目状态**: {summary['项目状态']}",
            f"- **总体进度**: {summary['总体进度']}",
            f"- **完成章节**: {summary['完成章节']}",
            f"- **当前章节**: 第{summary['当前章节']}回" if summary['当前章节'] else "无",
            f"- **总字数**: {summary['总字数']}",
            f"- **完成字数比例**: {summary['完成字数比例']}",
            f"- **平均每章字数**: {summary['平均每章字数']}",
            f"- **预估完成时间**: {summary['预估完成时间']}",
            "",
            "## 📋 章节详情",
            "",
            "| 章节 | 标题 | 状态 | 进度 | 字数 | 最后更新 |",
            "|------|------|------|------|------|----------|"
        ]
        
        for chapter in chapters:
            report_lines.append(
                f"| {chapter['章节']} | {chapter['标题']} | {chapter['状态']} | "
                f"{chapter['进度']} | {chapter['字数']} | {chapter['最后更新']} |"
            )
        
        # 添加统计图表
        completed = self.project_state.statistics.completed_chapters
        in_progress = self.project_state.statistics.in_progress_chapters
        not_started = 40 - completed - in_progress
        
        report_lines.extend([
            "",
            "## 📈 进度统计",
            "",
            f"- ✅ 已完成: {completed} 章节",
            f"- 🚧 进行中: {in_progress} 章节", 
            f"- ⏳ 未开始: {not_started} 章节",
            "",
            "## 🎯 里程碑进度",
            "",
            "```",
            f"总体完成度: {summary['总体进度']}",
            f"[{'█' * int(float(summary['总体进度'].rstrip('%')) // 5)}{'░' * (20 - int(float(summary['总体进度'].rstrip('%')) // 5))}]",
            "```",
            "",
            f"*报告生成于: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}*"
        ])
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                print(f"进度报告已保存到: {output_file}")
            except Exception as e:
                print(f"保存报告失败: {e}")
        
        return report_content
    
    def backup_state(self, backup_dir: str = "data/backups") -> str:
        """
        备份项目状态
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份文件路径
        """
        if not self.project_state:
            self.load_state()
        
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"project_state_backup_{timestamp}.json")
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_state.to_dict(), f, indent=2, ensure_ascii=False)
            return backup_file
        except Exception as e:
            print(f"备份失败: {e}")
            return ""
    
    def restore_state(self, backup_file: str) -> bool:
        """
        恢复项目状态
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            是否成功恢复
        """
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.project_state = ProjectState.from_dict(data)
                self.save_state()
                return True
        except Exception as e:
            print(f"恢复状态失败: {e}")
            return False

def create_progress_tracker(state_file: str = None) -> ProgressTracker:
    """
    创建进度跟踪器实例
    
    Args:
        state_file: 状态文件路径
        
    Returns:
        进度跟踪器实例
    """
    if state_file:
        return ProgressTracker(state_file)
    else:
        return ProgressTracker() 