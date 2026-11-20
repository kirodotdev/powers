# Symfony Code Simplification Guide

This guide covers Symfony-specific patterns, conventions,
and best practices for writing clean, maintainable code.

## Table of Contents

1. [Symfony Conventions](#symfony-conventions)
2. [Controller Best Practices](#controller-best-practices)
3. [Service Configuration](#service-configuration)
4. [Doctrine ORM](#doctrine-orm)
5. [Form Handling](#form-handling)
6. [Validation](#validation)
7. [Event System](#event-system)

---

## Symfony Conventions

### Directory Structure

Follow Symfony's standard directory structure:

```
src/
├── Controller/
├── Entity/
├── Repository/
├── Service/
├── Form/
├── EventListener/
├── EventSubscriber/
└── Kernel.php
```

### Naming Conventions

```php
// Controllers - Controller suffix
UserController, OrderController

// Entities - singular
User, Order, Product

// Repositories - Repository suffix
UserRepository, OrderRepository

// Services - descriptive names
EmailService, PaymentProcessor

// Form Types - Type suffix
UserType, OrderType
```

---

## Controller Best Practices

### Attribute-Based Routing (Symfony 6+)

```php
<?php

declare(strict_types=1);

namespace App\Controller;

use App\Entity\Order;
use App\Service\OrderService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

#[Route('/orders', name: 'order_')]
class OrderController extends AbstractController
{
    public function __construct(
        private OrderService $orderService
    ) {
    }

    #[Route('', name: 'index', methods: ['GET'])]
    public function index(): Response
    {
        $orders = $this->orderService->getAllOrders();

        return $this->render('order/index.html.twig', [
            'orders' => $orders,
        ]);
    }

    #[Route('/{id}', name: 'show', methods: ['GET'])]
    public function show(Order $order): Response
    {
        return $this->render('order/show.html.twig', [
            'order' => $order,
        ]);
    }

    #[Route('/create', name: 'create', methods: ['POST'])]
    public function create(Request $request): Response
    {
        $order = $this->orderService->createOrder(
            $request->request->all()
        );

        return $this->json($order, Response::HTTP_CREATED);
    }
}
```

### Thin Controllers

```php
// Bad - fat controller
class OrderController extends AbstractController
{
    #[Route('/orders', methods: ['POST'])]
    public function create(Request $request, EntityManagerInterface $em): Response
    {
        // Validation
        $data = $request->request->all();
        if (empty($data['items'])) {
            throw new BadRequestException('Items required');
        }

        // Business logic
        $total = 0;
        foreach ($data['items'] as $item) {
            $product = $em->getRepository(Product::class)->find($item['product_id']);
            $total += $product->getPrice() * $item['quantity'];
        }

        // Create order
        $order = new Order();
        $order->setUser($this->getUser());
        $order->setTotal($total);
        $order->setStatus('pending');

        $em->persist($order);
        $em->flush();

        return $this->json($order);
    }
}

// Good - thin controller with service
class OrderController extends AbstractController
{
    public function __construct(
        private OrderService $orderService
    ) {
    }

    #[Route('/orders', methods: ['POST'])]
    public function create(Request $request): Response
    {
        $order = $this->orderService->createOrder(
            user: $this->getUser(),
            items: $request->request->all('items')
        );

        return $this->json($order, Response::HTTP_CREATED);
    }
}
```

### ParamConverter for Automatic Entity Loading

```php
// Automatic entity loading from route parameters
#[Route('/orders/{id}', name: 'order_show')]
public function show(Order $order): Response
{
    // $order is automatically loaded by ID
    return $this->render('order/show.html.twig', [
        'order' => $order,
    ]);
}

// Custom field for loading
#[Route('/orders/{slug}', name: 'order_show_by_slug')]
public function showBySlug(
    #[MapEntity(mapping: ['slug' => 'slug'])]
    Order $order
): Response {
    return $this->render('order/show.html.twig', [
        'order' => $order,
    ]);
}
```

---

## Service Configuration

### Autowiring and Autoconfiguration

```yaml
# config/services.yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true

    App\:
        resource: "../src/"
        exclude:
            - "../src/DependencyInjection/"
            - "../src/Entity/"
            - "../src/Kernel.php"
```

### Service Constructor Injection

```php
// Use constructor injection for dependencies
class OrderService
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private OrderRepository $orderRepository,
        private EmailService $emailService,
        private LoggerInterface $logger
    ) {
    }

    public function createOrder(User $user, array $items): Order
    {
        try {
            $order = new Order();
            $order->setUser($user);
            $order->setTotal($this->calculateTotal($items));

            $this->entityManager->persist($order);
            $this->entityManager->flush();

            $this->emailService->sendOrderConfirmation($order);

            return $order;
        } catch (\Exception $e) {
            $this->logger->error('Order creation failed', [
                'user_id' => $user->getId(),
                'error' => $e->getMessage(),
            ]);
            throw $e;
        }
    }

    private function calculateTotal(array $items): float
    {
        // Calculate total logic
    }
}
```

### Service Aliases and Interfaces

```php
// Define interface
interface PaymentProcessorInterface
{
    public function process(Order $order): bool;
}

// Implementation
class StripePaymentProcessor implements PaymentProcessorInterface
{
    public function process(Order $order): bool
    {
        // Stripe payment logic
    }
}

// Configure in services.yaml
services:
    App\Service\PaymentProcessorInterface:
        alias: App\Service\StripePaymentProcessor

// Use in other services
class OrderService
{
    public function __construct(
        private PaymentProcessorInterface $paymentProcessor
    ) {
    }
}
```

---

## Doctrine ORM

### Entity Best Practices

```php
<?php

declare(strict_types=1);

namespace App\Entity;

use App\Repository\OrderRepository;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: OrderRepository::class)]
#[ORM\Table(name: 'orders')]
class Order
{
    #[ORM\Id]
    #[ORM\GeneratedValue]
    #[ORM\Column]
    private ?int $id = null;

    #[ORM\ManyToOne(targetEntity: User::class, inversedBy: 'orders')]
    #[ORM\JoinColumn(nullable: false)]
    private User $user;

    #[ORM\OneToMany(mappedBy: 'order', targetEntity: OrderItem::class, cascade: ['persist', 'remove'])]
    private Collection $items;

    #[ORM\Column(type: 'decimal', precision: 10, scale: 2)]
    private string $total;

    #[ORM\Column(length: 20)]
    private string $status = 'pending';

    #[ORM\Column]
    private \DateTimeImmutable $createdAt;

    public function __construct()
    {
        $this->items = new ArrayCollection();
        $this->createdAt = new \DateTimeImmutable();
    }

    // Getters and setters with proper type hints
    public function getId(): ?int
    {
        return $this->id;
    }

    public function getUser(): User
    {
        return $this->user;
    }

    public function setUser(User $user): self
    {
        $this->user = $user;
        return $this;
    }

    /**
     * @return Collection<int, OrderItem>
     */
    public function getItems(): Collection
    {
        return $this->items;
    }

    public function addItem(OrderItem $item): self
    {
        if (!$this->items->contains($item)) {
            $this->items->add($item);
            $item->setOrder($this);
        }

        return $this;
    }

    public function removeItem(OrderItem $item): self
    {
        if ($this->items->removeElement($item)) {
            if ($item->getOrder() === $this) {
                $item->setOrder(null);
            }
        }

        return $this;
    }

    public function getTotal(): string
    {
        return $this->total;
    }

    public function setTotal(string $total): self
    {
        $this->total = $total;
        return $this;
    }

    // Business logic methods
    public function isPending(): bool
    {
        return $this->status === 'pending';
    }

    public function markAsCompleted(): void
    {
        $this->status = 'completed';
    }
}
```

### Repository Patterns

```php
<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\Order;
use App\Entity\User;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class OrderRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, Order::class);
    }

    public function findRecentByUser(User $user, int $days = 30): array
    {
        return $this->createQueryBuilder('o')
            ->andWhere('o.user = :user')
            ->andWhere('o.createdAt >= :date')
            ->setParameter('user', $user)
            ->setParameter('date', new \DateTimeImmutable("-{$days} days"))
            ->orderBy('o.createdAt', 'DESC')
            ->getQuery()
            ->getResult();
    }

    public function findCompletedOrders(): array
    {
        return $this->createQueryBuilder('o')
            ->andWhere('o.status = :status')
            ->setParameter('status', 'completed')
            ->getQuery()
            ->getResult();
    }

    public function getTotalRevenue(): float
    {
        return (float) $this->createQueryBuilder('o')
            ->select('SUM(o.total)')
            ->andWhere('o.status = :status')
            ->setParameter('status', 'completed')
            ->getQuery()
            ->getSingleScalarResult();
    }
}
```

### Query Optimization

```php
// Bad - N+1 query problem
$orders = $orderRepository->findAll();
foreach ($orders as $order) {
    echo $order->getUser()->getName(); // Queries user for each order
}

// Good - eager loading with joins
$orders = $orderRepository->createQueryBuilder('o')
    ->leftJoin('o.user', 'u')
    ->addSelect('u')
    ->leftJoin('o.items', 'i')
    ->addSelect('i')
    ->getQuery()
    ->getResult();

// Partial objects for better performance
$orders = $orderRepository->createQueryBuilder('o')
    ->select('partial o.{id, total, status}')
    ->leftJoin('o.user', 'u')
    ->addSelect('partial u.{id, name, email}')
    ->getQuery()
    ->getResult();
```

---

## Form Handling

### Form Types

```php
<?php

declare(strict_types=1);

namespace App\Form;

use App\Entity\Order;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\CollectionType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class OrderType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options): void
    {
        $builder
            ->add('items', CollectionType::class, [
                'entry_type' => OrderItemType::class,
                'allow_add' => true,
                'allow_delete' => true,
                'by_reference' => false,
            ])
            ->add('submit', SubmitType::class, [
                'label' => 'Create Order',
            ]);
    }

    public function configureOptions(OptionsResolver $resolver): void
    {
        $resolver->setDefaults([
            'data_class' => Order::class,
        ]);
    }
}
```

### Form Handling in Controllers

```php
#[Route('/orders/new', name: 'order_new', methods: ['GET', 'POST'])]
public function new(Request $request, EntityManagerInterface $em): Response
{
    $order = new Order();
    $form = $this->createForm(OrderType::class, $order);

    $form->handleRequest($request);

    if ($form->isSubmitted() && $form->isValid()) {
        $em->persist($order);
        $em->flush();

        $this->addFlash('success', 'Order created successfully');

        return $this->redirectToRoute('order_show', ['id' => $order->getId()]);
    }

    return $this->render('order/new.html.twig', [
        'form' => $form,
    ]);
}
```

---

## Validation

### Validation Constraints

```php
<?php

namespace App\Entity;

use Symfony\Component\Validator\Constraints as Assert;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
class User
{
    #[ORM\Column(length: 180, unique: true)]
    #[Assert\NotBlank]
    #[Assert\Email]
    private string $email;

    #[Assert\NotBlank]
    #[Assert\Length(min: 8, max: 100)]
    private string $password;

    #[ORM\Column(length: 100)]
    #[Assert\NotBlank]
    #[Assert\Length(min: 2, max: 100)]
    private string $name;

    #[ORM\Column]
    #[Assert\Range(min: 18, max: 120)]
    private int $age;
}
```

### Custom Validation Constraints

```php
// Create custom constraint
<?php

namespace App\Validator;

use Symfony\Component\Validator\Constraint;

#[\Attribute]
class ValidCoupon extends Constraint
{
    public string $message = 'The coupon "{{ value }}" is not valid.';
}

// Create validator
<?php

namespace App\Validator;

use App\Repository\CouponRepository;
use Symfony\Component\Validator\Constraint;
use Symfony\Component\Validator\ConstraintValidator;

class ValidCouponValidator extends ConstraintValidator
{
    public function __construct(
        private CouponRepository $couponRepository
    ) {
    }

    public function validate($value, Constraint $constraint): void
    {
        if (null === $value || '' === $value) {
            return;
        }

        $coupon = $this->couponRepository->findActiveByCode($value);

        if (!$coupon) {
            $this->context->buildViolation($constraint->message)
                ->setParameter('{{ value }}', $value)
                ->addViolation();
        }
    }
}

// Use in entity
#[Assert\ValidCoupon]
private ?string $couponCode = null;
```

---

## Event System

### Event Subscribers

```php
<?php

declare(strict_types=1);

namespace App\EventSubscriber;

use App\Event\OrderCreatedEvent;
use App\Service\EmailService;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

class OrderSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private EmailService $emailService
    ) {
    }

    public static function getSubscribedEvents(): array
    {
        return [
            OrderCreatedEvent::class => 'onOrderCreated',
        ];
    }

    public function onOrderCreated(OrderCreatedEvent $event): void
    {
        $order = $event->getOrder();

        $this->emailService->sendOrderConfirmation($order);
    }
}
```

### Dispatching Events

```php
use Symfony\Contracts\EventDispatcher\EventDispatcherInterface;

class OrderService
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private EventDispatcherInterface $eventDispatcher
    ) {
    }

    public function createOrder(User $user, array $items): Order
    {
        $order = new Order();
        $order->setUser($user);
        // ... set other properties

        $this->entityManager->persist($order);
        $this->entityManager->flush();

        // Dispatch event
        $this->eventDispatcher->dispatch(
            new OrderCreatedEvent($order)
        );

        return $order;
    }
}
```

---

## Symfony Simplification Checklist

- [ ] Controllers are thin (business logic in services)
- [ ] Using attribute-based routing (Symfony 6+)
- [ ] Proper dependency injection via constructor
- [ ] Entity relationships properly configured
- [ ] Using QueryBuilder for complex queries
- [ ] Eager loading to avoid N+1 queries
- [ ] Form types for form handling
- [ ] Validation constraints on entities
- [ ] Event subscribers for cross-cutting concerns
- [ ] Repository methods for reusable queries
- [ ] Proper use of Doctrine cascade operations
- [ ] Type hints on all methods and properties

---

## Additional Resources

- Symfony Documentation:
  https://symfony.com/doc/current/index.html
- Symfony Best Practices:
  https://symfony.com/doc/current/best_practices.html
- Doctrine ORM Documentation:
  https://www.doctrine-project.org/projects/doctrine-orm/en/current/index.html

**Symfony Version Recommendation**: Use Symfony 6+ with PHP
8.1+ for best features and support.
