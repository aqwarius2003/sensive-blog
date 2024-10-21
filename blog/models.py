from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch


class PostQuerySet(models.QuerySet):
    def year(self, year):
        posts_at_year = self.filter(published_at__year=year).order_by('published_at')
        return posts_at_year

    def popular(self) -> 'PostQuerySet':
        """
        Return a QuerySet of posts sorted by the number of likes in descending order.

        Returns:
            PostQuerySet: A QuerySet of posts sorted by the number of likes in descending order.
        """
        posts_by_likes_count = self.annotate(likes_count=Count('likes')) \
            .order_by('-likes_count')
        return posts_by_likes_count

    def fetch_with_comments_count(self):
        """
        Fetch posts with comments count.

        Annotate each post object with an additional field 'comments_count' which
        contains the number of comments for this post.

        Returns:
            list: List of post objects each annotated with 'comments_count'.
        """
        posts_ids = [post.id for post in self]
        posts_with_comments_count_field = self.model.objects \
            .filter(id__in=posts_ids) \
            .annotate(comments_count=Count('comments'))
        ids_and_comments_count = (posts_with_comments_count_field
                                  .values_list('id', 'comments_count'))
        count_for_id = dict(ids_and_comments_count)
        for post in self:
            post.comments_count = count_for_id[post.id]
        return list(self)


    def prefetch_posts_count(self):
        """
        Возвращает QuerySet постов с предзагруженными авторами и тегами,
        аннотированными количеством постов.
        """
        return self.prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_count=Count('posts'))
            )
        )


class TagQuerySet(models.QuerySet):
    def popular(self):
        """
        Return a QuerySet of tags sorted by the number of posts in descending order.

        Returns:
            TagQuerySet: A QuerySet of tags sorted by the number of posts in descending order.
        """
        tags_by_post_count = self.annotate(posts_count=Count('posts')).order_by('-posts_count')
        return tags_by_post_count


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True}
    )
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги'
    )

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='comments')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'


