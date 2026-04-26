package com.example.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "ORDERS")
public class OrderEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
    @SequenceGenerator(name = "order_seq", sequenceName = "ORDER_SEQ")
    private Long id;

    @Column(columnDefinition = "VARCHAR2(20)")
    private String status;
}
